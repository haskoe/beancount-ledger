"""Domænemodeller for primobalance (primo.csv).

Svarende til spec afsnit 4.9.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import csv
from pydantic import BaseModel, Field, field_validator


class PrimoEntry(BaseModel):
    """Én primopostering."""

    beancount_account: str = Field(
        ...,
        min_length=1,
        description="Fuldt beancount-kontonavn, fx 'Income:DK:1010:Varesalg:Momspligtigt'",
    )
    amount: Decimal

    @field_validator("beancount_account", mode="before")
    @classmethod
    def account_strip(cls, v: object) -> str:
        return str(v).strip()


class PrimoFile(BaseModel):
    """Primobalance, indlæst fra primo.csv."""

    entries: list[PrimoEntry] = Field(default_factory=list)

    @classmethod
    def from_csv(cls, path: Path) -> PrimoFile:
        """Indlæs kontoplan fra en semikolon-separeret CSV-fil."""
        rows: list[PrimoEntry] = []
        with path.open(encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh, delimiter=";")
            for row in reader:
                rows.append(row)
        return cls(entries = rows)

    def is_balanced(self) -> bool:
        """Kontroller om primo-posteringerne balancerer (sum == 0)."""
        return sum(e.amount for e in self.entries) == Decimal("0")
