"""Domænemodeller for lønkørsler (data/<YYYY>/loen.yaml).

Svarende til spec afsnit 4.6.
Forretningsregel BR-L01: net_salary = gross_salary − tax − atp_employee.
"""

from __future__ import annotations

import datetime
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator

_CENT = Decimal("0.01")


class SalaryRun(BaseModel):
    """Én lønkørsel fra loen.yaml."""

    run_date: datetime.date
    employee_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    gross_salary: Decimal = Field(..., ge=Decimal("0"))
    tax: Decimal = Field(..., ge=Decimal("0"))
    atp_employee: Decimal = Field(..., ge=Decimal("0"))
    atp_employer: Decimal = Field(..., ge=Decimal("0"))
    net_salary: Decimal = Field(..., ge=Decimal("0"))
    period: str = Field(..., min_length=1)

    @field_validator("run_date", mode="before")
    @classmethod
    def _parse_date(cls, v: object) -> datetime.date:
        if isinstance(v, datetime.date):
            return v
        return datetime.date.fromisoformat(str(v).strip())

    @field_validator("employee_id", "name", "period", mode="before")
    @classmethod
    def _strip(cls, v: object) -> str:
        return str(v).strip()

    @model_validator(mode="after")
    def _check_net_salary(self) -> SalaryRun:
        """BR-L01: gross_salary − tax − atp_employee == net_salary (afrundet til øre)."""
        expected = (self.gross_salary - self.tax - self.atp_employee).quantize(
            _CENT, ROUND_HALF_UP
        )
        actual = self.net_salary.quantize(_CENT, ROUND_HALF_UP)
        if expected != actual:
            raise ValueError(
                f"net_salary {actual} stemmer ikke: "
                f"gross_salary({self.gross_salary}) − tax({self.tax}) − "
                f"atp_employee({self.atp_employee}) = {expected}"
            )
        return self

    def transaction_id(self) -> str:
        """Returnér transaction ID (BR-L03)."""
        return f"salary;{self.run_date};{self.employee_id}"


class SalaryFile(BaseModel):
    """Samling af lønkørsler, indlæst fra loen.yaml."""

    runs: list[SalaryRun] = Field(default_factory=list)

    @classmethod
    def from_yaml(cls, path: Path) -> SalaryFile:
        """Indlæs lønfil fra loen.yaml."""
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        return cls.model_validate(data or {})
