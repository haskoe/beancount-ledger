"""Domænemodeller for primobalance (primo.csv).

Svarende til spec afsnit 4.9.
"""

from __future__ import annotations

import datetime
from decimal import Decimal
from pathlib import Path

import yaml
from pydantic import BaseModel, Field, field_validator


class PrimoEntry(BaseModel):
    """Én primopostering."""

    account: str = Field(..., min_length=1)
    amount: Decimal
    description: str = ""

    @field_validator("account", mode="before")
    @classmethod
    def _strip(cls, v: object) -> str:
        return str(v).strip()


class PrimoFile(BaseModel):
    """Primobalance, indlæst fra primo.csv."""

    date: datetime.date
    entries: list[PrimoEntry] = Field(default_factory=list)

    @field_validator("date", mode="before")
    @classmethod
    def _parse_date(cls, v: object) -> datetime.date:
        if isinstance(v, datetime.date):
            return v
        return datetime.date.fromisoformat(str(v).strip())

    @classmethod
    def from_yaml(cls, path: Path) -> PrimoFile:
        """Indlæs primofil fra primo.csv."""
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        return cls.model_validate(data or {})

    def is_balanced(self) -> bool:
        """Kontroller om primo-posteringerne balancerer (sum == 0)."""
        return sum(e.amount for e in self.entries) == Decimal("0")
