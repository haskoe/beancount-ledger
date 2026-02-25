"""Domænemodeller for ydelseskatalog (ydelser.yaml).

Svarende til spec afsnit 4.4.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import yaml
from pydantic import BaseModel, Field, field_validator


class Service(BaseModel):
    """Én ydelse/produkt fra ydelser.yaml."""

    service_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    standard_price: Decimal = Field(..., ge=Decimal("0"))
    unit: str = Field(default="stk", min_length=1)
    vat_applicable: bool = True
    income_account: str = Field(..., min_length=1)

    @field_validator("service_id", "name", "income_account", mode="before")
    @classmethod
    def _strip(cls, v: object) -> str:
        return str(v).strip()


class ServiceCatalog(BaseModel):
    """Samling af ydelser, indlæst fra ydelser.yaml."""

    services: list[Service] = Field(default_factory=list)

    # ------------------------------------------------------------------
    # Fabriksmetoder
    # ------------------------------------------------------------------

    @classmethod
    def from_yaml(cls, path: Path) -> ServiceCatalog:
        """Indlæs ydelseskataloget fra ydelser.yaml."""
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        return cls.model_validate(data or {})

    # ------------------------------------------------------------------
    # Opslag
    # ------------------------------------------------------------------

    def by_id(self, service_id: str) -> Service | None:
        """Returner ydelse med det givne id, eller None."""
        needle = service_id.strip()
        return next((s for s in self.services if s.service_id == needle), None)
