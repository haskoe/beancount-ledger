"""Application service: opret et nyt firma-repo (T-21).

Workflow:
    1. Opret rod + standard mappestruktur (company_layout.ensure_dirs).
    2. Kopier rod-niveau konfigurationsskabeloner (render settings.yaml og
       pyproject.toml med firm-specifikke variable).
    3. Generer kontoplan.beancount fra standardkontoplan.csv.
    4. Initialisér git-repo og lav "initial commit".

Eksisterende filer overskrives aldrig.
"""

from __future__ import annotations

import importlib.resources
from pathlib import Path

from beancount_ledger.application.kontoplan_service import generate_kontoplan
from beancount_ledger.infrastructure import company_layout, git_io

# ---------------------------------------------------------------------------
# Skabelon-mapping: (skabelonfilnavn, destinationsfilnavn i firma-roden)
# ---------------------------------------------------------------------------
_ROOT_TEMPLATES: list[tuple[str, str]] = [
    ("settings.yaml", "settings.yaml"),
    ("primo.csv", "primo.csv"),
    ("sales_accounts.yaml", "sales_accounts.yaml"),
    ("standardkontoplan.csv", "standardkontoplan.csv"),
    ("current.yaml", "current.yaml"),
    ("ydelser.yaml", "ydelser.yaml"),    
    ("bank_keywords.yaml", "bank_keywords.yaml"),    
    ("firma_gitignore.txt", ".gitignore"),
#    ("firma_pyproject.toml.txt", "pyproject.toml"),
    ("regnskab.beancount", "regnskab.beancount"),
]

# Disse skabeloner indeholder {placeholder}-variable der skal erstattes.
_RENDERED: frozenset[str] = frozenset({"settings.yaml", "firma_pyproject.toml.txt"})


def create_company(
    root: Path,
    cvr: str,
) -> None:
    """Opret et nyt firma-repo under *root*.

    Args:
        root:         Absolut sti til firma-repoets rod (oprettes hvis den ikke
                      eksisterer).
        cvr:          CVR-nummer der indsættes i settings.yaml og pyproject.toml.
    """
    root.mkdir(parents=True, exist_ok=True)
    company_layout.ensure_dirs(root)

    substitutions = {
        "cvr": cvr,
    }

    templates_pkg = importlib.resources.files("beancount_ledger.infrastructure.templates")

    for template_name, dest_name in _ROOT_TEMPLATES:
        dest = root / dest_name
        if dest.exists():
            continue  # overskriv aldrig eksisterende filer

        content = (templates_pkg / template_name).read_text(encoding="utf-8")
        if template_name in _RENDERED:
            for key, value in substitutions.items():
                content = content.replace("{" + key + "}", value)
        dest.write_text(content, encoding="utf-8")

    generate_kontoplan(root)

    # Kopier navntilkonto.csv til forældremappen (delt på tværs af firmaer).
    # Overskrives aldrig så eksisterende tilpasninger bevares.
    shared_nametable = root.parent / "navntilkonto.csv"
    if not shared_nametable.exists():
        templates_pkg2 = importlib.resources.files("beancount_ledger.infrastructure.templates")
        shared_nametable.write_text(
            (templates_pkg2 / "navntilkonto.csv").read_text(encoding="utf-8"),
            encoding="utf-8",
        )

    git_io.init_repo(root)
    git_io.commit_all(root, "initial commit")
