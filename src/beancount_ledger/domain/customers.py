"""Domænemodeller for kundekatalog (sales_accounts.yaml).

Svarende til spec afsnit 4.3.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import yaml
from pydantic import BaseModel, Field, field_validator


class Customer(BaseModel):
    """Én kunde fra sales_accounts.yaml."""

    customer_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    cvr: str | None = Field(default=None, pattern=r"^\d{8}$")
    beancount_account: str = Field(..., min_length=1)
    email: str | None = None
    payment_days: Annotated[int, Field(ge=1, le=365)] = 30

    @field_validator("customer_id", "name", "beancount_account", mode="before")
    @classmethod
    def _strip(cls, v: object) -> str:
        return str(v).strip()

    @field_validator("cvr", mode="before")
    @classmethod
    def _cvr_strip(cls, v: object) -> str | None:
        if v is None:
            return None
        stripped = str(v).strip()
        return stripped if stripped else None


class CustomerRegister(BaseModel):
    """Samling af kunder, indlæst fra sales_accounts.yaml."""

    customers: list[Customer] = Field(default_factory=list)

    # ------------------------------------------------------------------
    # Fabriksmetoder
    # ------------------------------------------------------------------

    @classmethod
    def from_yaml(cls, path: Path) -> CustomerRegister:
        """Indlæs kunderegistret fra sales_accounts.yaml."""
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        return cls.model_validate(data or {})

    # ------------------------------------------------------------------
    # Opslag
    # ------------------------------------------------------------------

    def by_id(self, customer_id: str) -> Customer | None:
        """Returner kunde med det givne id, eller None."""
        needle = customer_id.strip()
        return next((c for c in self.customers if c.customer_id == needle), None)
