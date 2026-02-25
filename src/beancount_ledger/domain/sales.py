"""Domænemodeller for salgsfakturaer (data/<YYYY>/salg.yaml).

Svarende til spec afsnit 4.5.
Forretningsregler: BR-S01 til BR-S07.
"""

from __future__ import annotations

import datetime
from decimal import Decimal
from pathlib import Path

import yaml
from pydantic import BaseModel, Field, field_validator

VAT_RATE = Decimal("0.25")


class InvoiceLine(BaseModel):
    """Én linje på en salgsfaktura."""

    service_id: str = Field(..., min_length=1)
    quantity: Decimal = Field(..., gt=Decimal("0"))
    price_override: Decimal | None = Field(default=None, ge=Decimal("0"))

    @field_validator("service_id", mode="before")
    @classmethod
    def _strip(cls, v: object) -> str:
        return str(v).strip()

    def effective_price(self, standard_price: Decimal) -> Decimal:
        """Returner gældende enhedspris (BR-S03)."""
        return self.price_override if self.price_override is not None else standard_price

    def line_total(self, standard_price: Decimal) -> Decimal:
        """Returner linjens beløb ekskl. moms (BR-S04)."""
        return self.quantity * self.effective_price(standard_price)


class Invoice(BaseModel):
    """Én salgsfaktura fra salg.yaml."""

    invoice_number: str = Field(..., min_length=1)
    invoice_date: datetime.date
    customer_id: str = Field(..., min_length=1)
    template: str = "default"
    lines: list[InvoiceLine] = Field(default_factory=list)

    @field_validator("invoice_number", "customer_id", mode="before")
    @classmethod
    def _strip(cls, v: object) -> str:
        return str(v).strip()

    @field_validator("invoice_date", mode="before")
    @classmethod
    def _parse_date(cls, v: object) -> datetime.date:
        if isinstance(v, datetime.date):
            return v
        return datetime.date.fromisoformat(str(v).strip())

    def transaction_id(self) -> str:
        """Returnér transaction ID (BR-S07)."""
        return f"sales;{self.invoice_number}"


class SalesFile(BaseModel):
    """Samling af salgsfakturaer, indlæst fra salg.yaml."""

    invoices: list[Invoice] = Field(default_factory=list)

    @classmethod
    def from_yaml(cls, path: Path) -> SalesFile:
        """Indlæs salgsfil fra salg.yaml."""
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        return cls.model_validate(data or {})

    def by_invoice_number(self, invoice_number: str) -> Invoice | None:
        """Returner faktura med det givne fakturanummer, eller None."""
        needle = invoice_number.strip()
        return next((i for i in self.invoices if i.invoice_number == needle), None)
