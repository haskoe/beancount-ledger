"""Application service: initialisér et nyt regnskabsår (T-22).

Opretter `data/<YYYY>/` med tomme skabelonfiler og committer.
Kaldes automatisk i update-flowet hvis mappen ikke eksisterer endnu.
"""

from __future__ import annotations

import importlib.resources
from pathlib import Path

from beancount_ledger.infrastructure import company_layout, git_io

# ---------------------------------------------------------------------------
# (skabelonfilnavn, destinationsfilnavn i data/<YYYY>/, render_year)
# ---------------------------------------------------------------------------
_YEAR_TEMPLATES: list[tuple[str, str, bool]] = [
    ("salg.yaml", "salg.yaml", True),
    ("loen.yaml", "loen.yaml", True),
    ("udbytte.yaml", "udbytte.yaml", True),
    ("bank.csv", "bank.csv", False),
]


def init_year(root: Path, year: int) -> bool:
    """Opret `data/<year>/` med tomme skabelonfiler og commit.

    Args:
        root: Firma-repoets rod.
        year: Regnskabsåret der skal initialiseres.

    Returns:
        True hvis mappen blev oprettet, False hvis den allerede eksisterede.
    """
    year_dir = company_layout.data_dir(root, year)
    if year_dir.exists():
        return False

    year_dir.mkdir(parents=True, exist_ok=True)

    substitutions = {"year": str(year)}
    templates_pkg = importlib.resources.files("beancount_ledger.infrastructure.templates")

    for template_name, dest_name, render in _YEAR_TEMPLATES:
        dest = year_dir / dest_name
        content = (templates_pkg / template_name).read_text(encoding="utf-8")
        if render:
            for key, value in substitutions.items():
                content = content.replace("{" + key + "}", value)
        dest.write_text(content, encoding="utf-8")

    git_io.commit_all(root, f"year {year} created")
    return True
