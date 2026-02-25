"""Domænemodeller for current.yaml (auto-genereret tilstandsfil).

Svarende til spec afsnit 4.11.
"""

from __future__ import annotations

import datetime
from pathlib import Path

import yaml
from pydantic import BaseModel, Field, field_validator


class CurrentState(BaseModel):
    """Aktuel regnskabstilstand, gemt i current.yaml."""

    current_year: int | None = None
    current_vat_period: str | None = None

    @field_validator("current_vat_period", mode="before")
    @classmethod
    def _strip(cls, v: object) -> str:
        return str(v).strip()

    # ------------------------------------------------------------------
    # Fabriksmetoder
    # ------------------------------------------------------------------

    @classmethod
    def from_yaml(cls, path: Path) -> CurrentState:
        """Indlæs current.yaml."""
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        return cls.model_validate(data or {})

    def to_yaml(self, path: Path) -> None:
        """Gem current.yaml (overskriv)."""
        raw = self.model_dump(mode="json")
        path.write_text(yaml.dump(raw, allow_unicode=True, sort_keys=False), encoding="utf-8")
