"""Domænemodeller for audit-fil (generated/audit.yaml).

Svarende til spec afsnit 4.10.
Audit-filen er den ENESTE kilde til draft/approved-status (BR-A01).
"""

from __future__ import annotations

import datetime
from decimal import Decimal
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, field_validator

AuditStatus = Literal["draft", "approved"]


class AuditEntry(BaseModel):
    """Én audit-post — én postering med status og metadata."""

    transaction_id: str = Field(..., min_length=1)
    account: str = Field(..., min_length=1)
    date: datetime.date
    vat_free_amount: Decimal = Decimal("0")
    receipt: str = ""
    notes: str = ""

    @field_validator("date", mode="before")
    @classmethod
    def _parse_date(cls, v: object) -> datetime.date:
        if isinstance(v, datetime.date):
            return v
        return datetime.date.fromisoformat(str(v).strip())

    @field_validator("transaction_id", "account", mode="before")
    @classmethod
    def _strip(cls, v: object) -> str:
        return str(v).strip()


class AuditFile(BaseModel):
    """Samling af audit-poster, indlæst fra / gemt i generated/audit.yaml."""

    entries: list[AuditEntry] = Field(default_factory=list)

    # ------------------------------------------------------------------
    # Fabriksmetoder
    # ------------------------------------------------------------------

    @classmethod
    def from_yaml(cls, path: Path) -> AuditFile:
        """Indlæs audit-fil. Returnerer tom fil hvis path ikke eksisterer."""
        if not path.exists():
            return cls()
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        return cls.model_validate(data or {})

    def to_yaml(self, path: Path) -> None:
        """Gem audit-fil til YAML (overskriv)."""
        raw = self.model_dump(mode="json")
        path.write_text(yaml.dump(raw, allow_unicode=True, sort_keys=False), encoding="utf-8")

    # ------------------------------------------------------------------
    # Opslag og filtrering
    # ------------------------------------------------------------------

    def by_transaction_id(self, transaction_id: str) -> AuditEntry | None:
        """Returner post med det givne transaction ID, eller None."""
        return next((e for e in self.entries if e.transaction_id == transaction_id), None)

    def drafts(self) -> list[AuditEntry]:
        """Returnér alle poster med status 'draft'."""
        return [e for e in self.entries if e.status == "draft"]

    def has_drafts(self) -> bool:
        """Returnér True hvis der er draft-posteringer."""
        return any(e.status == "draft" for e in self.entries)

    # ------------------------------------------------------------------
    # Ændringer
    # ------------------------------------------------------------------

    def add(self, entry: AuditEntry) -> None:
        """Tilføj en ny post (duplikat-check på transaction_id)."""
        if self.by_transaction_id(entry.transaction_id) is not None:
            raise ValueError(f"Duplikat transaction_id: {entry.transaction_id!r}")
        self.entries.append(entry)

    def approve_all(self) -> int:
        """Sæt alle draft-poster til 'approved'. Returnerer antal opdaterede."""
        count = 0
        for entry in self.entries:
            if entry.status == "draft":
                entry.status = "approved"
                count += 1
        return count
