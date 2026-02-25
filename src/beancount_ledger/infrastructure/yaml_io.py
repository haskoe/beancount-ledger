"""Generisk YAML I/O til firma-repo-filer.

Bruges af application-laget til at indlæse/gemme alle YAML-filer.
Alle stier skal bruge pathlib.Path (BR-03).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_yaml(path: Path) -> dict[str, Any]:
    """Indlæs en YAML-fil og returnér indholdet som dict.

    Returnerer tomt dict hvis filen er tom eller ikke eksisterer
    (eksistens-check overlades til kalderen — brug `path.exists()` beforehand).
    """
    text = path.read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError(f"Forventet dict øverst i {path}, fik {type(data).__name__}")
    return data  # type: ignore[return-value]


def save_yaml(path: Path, data: dict[str, Any]) -> None:
    """Gem data som YAML-fil (overskriv).

    Opretter forældremappe automatisk hvis den ikke eksisterer.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.dump(data, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
