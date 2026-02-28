from __future__ import annotations

import csv
import importlib.resources as ir
from functools import cached_property
from pathlib import Path

from pydantic import BaseModel, Field, field_validator


class NameMapping(BaseModel):
    """Én navn-til-konto mapping fra navntilkonto.csv."""

    name: str = Field(..., min_length=1, description="Navn eller beskrivelse, fx 'Telmore'")
    beancount_account: str = Field(
        ...,
        min_length=1,
        description="Fuldt beancount-kontonavn, fx 'Expenses:DK:3130:Telefoni-Internet'",
    )

    @field_validator("name", mode="before")
    @classmethod
    def name_strip(cls, v: object) -> str:
        return str(v).strip()

    @field_validator("beancount_account", mode="before")
    @classmethod
    def account_strip(cls, v: object) -> str:
        return str(v).strip()


class NameToAccount(BaseModel):
    """Samling af navn-til-konto mappings, indlæst fra navntilkonto.csv."""

    mappings: list[NameMapping] = Field(default_factory=list)

    # ------------------------------------------------------------------
    # Fabriksmetoder
    # ------------------------------------------------------------------
    @classmethod
    def from_csv(cls, path: Path) -> NameToAccount:
        """Indlæs navn-til-konto mapping fra en semikolon-separeret CSV-fil."""
        rows: list[NameMapping] = []
        with path.open(encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh, delimiter=";")
            for row in reader:
                rows.append(NameMapping.model_validate(row))
        return cls(mappings=rows)

    @classmethod
    def from_builtin(cls) -> NameToAccount:
        """Indlæs standard navntilkonto.csv bundlet med app-pakken."""
        pkg = ir.files("beancount_ledger.infrastructure.templates")
        csv_bytes = (pkg / "navntilkonto.csv").read_bytes()
        import io

        rows: list[NameMapping] = []
        fh = io.StringIO(csv_bytes.decode("utf-8"))
        reader = csv.DictReader(fh, delimiter=";")
        for row in reader:
            rows.append(NameMapping.model_validate(row))
        return cls(mappings=rows)

    # ------------------------------------------------------------------
    # Opslag
    # ------------------------------------------------------------------

    def by_name(self, name: str) -> str | None:
        """Returner beancount-konto for det givne navn, eller None."""
        needle = name.strip()
        mapping = next((m for m in self.mappings if m.name == needle), None)
        return mapping.beancount_account if mapping else None

    def get_matching_accounts(self, description):
        description_lower = description.lower()
        return [m for m in self.mappings if m.name.lower() in description_lower]

    def all_names(self) -> list[str]:
        """Returnér en sorteret liste af alle navne."""
        return sorted(m.name for m in self.mappings)

    def all_accounts(self) -> list[str]:
        """Returnér en sorteret liste af alle beancount-kontonavne."""
        return sorted(m.beancount_account for m in self.mappings)
