"""Git-wrapper til at finde nye linjer i sporerede filer (BR-06).

Bruges af application-services til at opdage nye rækker i
salg.yaml, loen.yaml, udbytte.yaml og bank.csv.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


class GitError(Exception):
    """Fejl ved git-kald."""


def _run_git(args: list[str], cwd: Path) -> str:
    """Kør git-kommando og returnér stdout. Kast GitError ved fejl."""
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise GitError(f"git {' '.join(args)} fejlede: {result.stderr.strip()}")
    return result.stdout


def is_tracked(path: Path) -> bool:
    """Returnér True hvis filen er sporeret af git (committed eller staged)."""
    result = subprocess.run(
        ["git", "ls-files", "--error-unmatch", str(path)],
        cwd=path.parent,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def get_new_lines(path: Path, repo_root: Path | None = None) -> list[str]:
    """Returnér nye linjer i `path` relativt til HEAD.

    Logik:
    - Hvis filen ikke er sporeret (untracked/ny): returnér alle ikke-tomme linjer.
    - Hvis filen er sporeret og uændret: returnér tom liste.
    - Hvis filen er sporeret og ændret: returnér de linjer som `git diff HEAD` tilføjer
      (dvs. `+`-linjer ekskl. diff-header-linjer der starter med `+++`).

    `repo_root` bruges som cwd for git. Hvis None, bruges `path.parent`.
    """
    cwd = repo_root if repo_root is not None else path.parent

    if not is_tracked(path):
        # Filen er ny — alle linjer er "nye"
        return [
            line
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    diff_output = _run_git(["diff", "HEAD", "--", str(path)], cwd=cwd)

    if not diff_output.strip():
        # Ingen ændringer
        return []

    new_lines: list[str] = []
    for line in diff_output.splitlines():
        if line.startswith("+") and not line.startswith("+++"):
            new_lines.append(line[1:])  # fjern det ledende '+'
    return new_lines


def commit_all(repo_root: Path, message: str) -> bool:
    """Stage alle ændrede/nye filer i firma-repoet og commit.

    Returnerer True hvis commit lykkedes, False hvis der ikke var noget at committe.
    Kaster GitError ved andre git-fejl.
    """
    _run_git(["add", "-A"], cwd=repo_root)
    # Tjek om der er noget staged
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if not result.stdout.strip():
        return False  # intet at committe
    _run_git(["commit", "-m", message], cwd=repo_root)
    return True


def init_repo(path: Path) -> None:
    """Initialisér et nyt git-repo i `path` (git init + initial commit)."""
    _run_git(["init"], cwd=path)
    _run_git(["config", "user.email", "beancount_ledger@example.com"], cwd=path)
    _run_git(["config", "user.name", "beancount_ledger"], cwd=path)
