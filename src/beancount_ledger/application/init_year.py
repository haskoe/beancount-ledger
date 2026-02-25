"""Application service: initialisér et nyt regnskabsår (T-22).

Opretter `data/<YYYY>/` med tomme skabelonfiler og committer.
Kaldes automatisk i update-flowet hvis mappen ikke eksisterer endnu.
"""

from __future__ import annotations

from beancount_ledger.application.app_context import AppContext
from beancount_ledger.infrastructure import git_io

# ---------------------------------------------------------------------------
# (skabelonfilnavn, destinationsfilnavn i data/<YYYY>/, render_year)
# ---------------------------------------------------------------------------
_YEAR_TEMPLATES: list[tuple[str, str, bool]] = [
    ("salg.yaml", "salg.yaml", True),
    ("loen.yaml", "loen.yaml", True),
    ("udbytte.yaml", "udbytte.yaml", True),
    ("bank.csv", "bank.csv", False),
]


def init_year(app_context: AppContext) -> bool:
    current_year = app_context.current_state.current_year
    year_path = app_context.get_year_dir(current_year)

    substitutions = {"year": str(current_year)}
    templates_pkg = importlib.resources.files("beancount_ledger.infrastructure.templates")

    for template_name, dest_name, render in _YEAR_TEMPLATES:
        dest = year_path / dest_name
        content = (templates_pkg / template_name).read_text(encoding="utf-8")
        if render:
            for key, value in substitutions.items():
                content = content.replace("{" + key + "}", value)
        dest.write_text(content, encoding="utf-8")

    git_io.commit_all(app_context.root_path, f"year {current_year} created")
    return True
