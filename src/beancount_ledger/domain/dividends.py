"""Domænemodeller for udbytteudbetalinger (data/<YYYY>/udbytte.yaml).

Svarende til spec afsnit 4.7.
Forretningsregel BR-U01: net_amount = gross_amount − withholding_tax.
"""

from __future__ import annotations

import datetime
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator

_CENT = Decimal("0.01")

STANDARD_WITHHOLDING_RATE = Decimal("0.27")  # BR-U02


class DividendPayment(BaseModel):
    """Én udbytteudbetaling fra udbytte.yaml."""

    run_date: datetime.date
    recipient_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    gross_amount: Decimal = Field(..., ge=Decimal("0"))
    withholding_tax: Decimal = Field(..., ge=Decimal("0"))
    net_amount: Decimal = Field(..., ge=Decimal("0"))

    @field_validator("run_date", mode="before")
    @classmethod
    def _parse_date(cls, v: object) -> datetime.date:
        if isinstance(v, datetime.date):
            return v
        return datetime.date.fromisoformat(str(v).strip())

    @field_validator("recipient_id", "name", mode="before")
    @classmethod
    def _strip(cls, v: object) -> str:
        return str(v).strip()

    @model_validator(mode="after")
    def _check_net_amount(self) -> DividendPayment:
        """BR-U01: gross_amount − withholding_tax == net_amount (afrundet til øre)."""
        expected = (self.gross_amount - self.withholding_tax).quantize(_CENT, ROUND_HALF_UP)
        actual = self.net_amount.quantize(_CENT, ROUND_HALF_UP)
        if expected != actual:
            raise ValueError(
                f"net_amount {actual} stemmer ikke: "
                f"gross_amount({self.gross_amount}) − "
                f"withholding_tax({self.withholding_tax}) = {expected}"
            )
        return self

    def transaction_id(self) -> str:
        """Returnér transaction ID (BR-U03)."""
        return f"dividend;{self.run_date};{self.recipient_id}"


class DividendsFile(BaseModel):
    """Samling af udbytteudbetalinger, indlæst fra udbytte.yaml."""

    payments: list[DividendPayment] = Field(default_factory=list)

    @classmethod
    def from_yaml(cls, path: Path) -> DividendsFile:
        """Indlæs udbyttefil fra udbytte.yaml."""
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        return cls.model_validate(data or {})
