"""Domænemodeller for standardkontoplan (chart of accounts).

Kolonner i standardkontoplan.csv (semikolon-separeret):
    id;beancount_account;description;default_vat
"""

from __future__ import annotations

import csv
import importlib.resources as ir
from pathlib import Path

from pydantic import BaseModel, Field, field_validator

# Kendte momskoder — udvides her hvis nødvendigt.
# S25  = salgsmoms 25 % (udgående)
# I25  = købsmoms 25 % (indgående, fuld fradragsret)
# EU25 = EU/import omvendt betalingspligt 25 %
# R25  = repræsentation 25 % (kun 25 % fradragsret)
# N0   = ingen moms
KNOWN_VAT_CODES = {"S25", "I25", "EU25", "R25", "N0"}


class Account(BaseModel):
    """Én konto fra standardkontoplan.csv."""

    id: str = Field(..., min_length=1, description="Kontonummer (tekststreng, fx '1010')")
    beancount_account: str = Field(
        ...,
        min_length=1,
        description="Fuldt beancount-kontonavn, fx 'Income:DK:1010:Varesalg:Momspligtigt'",
    )
    description: str = Field(..., min_length=1, description="Dansk kontobeskrivelse")
    default_vat: str = Field(..., description="Standardmomskode, fx 'S25' eller 'N0'")

    @field_validator("id", mode="before")
    @classmethod
    def id_strip(cls, v: object) -> str:
        return str(v).strip()

    @field_validator("beancount_account", mode="before")
    @classmethod
    def account_strip(cls, v: object) -> str:
        return str(v).strip()

    @field_validator("description", mode="before")
    @classmethod
    def description_strip(cls, v: object) -> str:
        return str(v).strip()

    @field_validator("default_vat", mode="before")
    @classmethod
    def vat_upper_strip(cls, v: object) -> str:
        return str(v).strip().upper()


class ChartOfAccounts(BaseModel):
    """Samling af alle konti, indlæst fra standardkontoplan.csv."""

    accounts: list[Account] = Field(default_factory=list)

    # ------------------------------------------------------------------
    # Fabriksmetoder
    # ------------------------------------------------------------------

    @classmethod
    def from_csv(cls, path: Path) -> ChartOfAccounts:
        """Indlæs kontoplan fra en semikolon-separeret CSV-fil."""
        rows: list[Account] = []
        with path.open(encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh, delimiter=";")
            for row in reader:
                rows.append(Account.model_validate(row))
        return cls(accounts=rows)

    @classmethod
    def from_builtin(cls) -> ChartOfAccounts:
        """Indlæs standardkontoplan bundlet med app-pakken."""
        pkg = ir.files("beancount_ledger.infrastructure.templates")
        csv_bytes = (pkg / "standardkontoplan.csv").read_bytes()
        import io

        rows: list[Account] = []
        fh = io.StringIO(csv_bytes.decode("utf-8"))
        reader = csv.DictReader(fh, delimiter=";")
        for row in reader:
            rows.append(Account.model_validate(row))
        return cls(accounts=rows)

    # ------------------------------------------------------------------
    # Opslag
    # ------------------------------------------------------------------
    def get_matching_accounts(self, account_name):
        _account_name = account_name.lower()
        return [a for a in self.accounts if _account_name in a.beancount_account]

    def by_id(self, account_id: str) -> Account | None:
        """Returner konto med det givne kontonummer, eller None."""
        needle = account_id.strip()
        return next((a for a in self.accounts if a.id == needle), None)

    def by_beancount_account(self, beancount_account: str) -> Account | None:
        """Returner konto med det givne beancount-kontonavn, eller None."""
        needle = beancount_account.strip()
        return next((a for a in self.accounts if a.beancount_account == needle), None)

    def all_beancount_accounts(self) -> list[str]:
        """Returnér en sorteret liste af alle beancount-kontonavne."""
        return sorted(a.beancount_account for a in self.accounts)

    # ------------------------------------------------------------------
    # Validering
    # ------------------------------------------------------------------

    def unknown_vat_codes(self) -> list[tuple[str, str]]:
        """Returner liste af (id, default_vat) for ukendte momskoder."""
        return [
            (a.id, a.default_vat) for a in self.accounts if a.default_vat not in KNOWN_VAT_CODES
        ]
