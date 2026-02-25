"""Domænemodel for firma-indstillinger (settings.yaml)."""

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class BankCsvFormat(BaseModel):
    """Konfiguration af bankens CSV-eksportformat."""

    date_column: str = "Date"
    description_column: str = "Tekst"
    amount_column: str = "Amount"
    balance_column: str = "Saldo"
    date_format: str = "%d-%m-%Y"
    decimal_separator: Literal[",", "."] = ","
    encoding: str = "utf-8"


class BankDownloadFormat(BaseModel):
    """Konfiguration af bankens rå download-CSV (før transformation).

    Bruges af ``import-bank``-kommandoen til at kortlægge bankens eksport til
    applikationens interne bank.csv-format.
    """

    has_header: bool = False
    """Om bankfilen har en header-række der skal springes over."""

    date_col: int = 0
    """Kolonneindeks (0-baseret) for dato."""

    text_col: int = 1
    """Kolonneindeks for beskrivelse/tekst."""

    amount_col: int = 2
    """Kolonneindeks for beløb."""

    balance_col: int = 3
    """Kolonneindeks for saldo."""

    date_format: str = "%d-%m-%Y"
    """Datoformat i bankfilen."""

    decimal_separator: Literal[",", "."] = ","
    """Decimalseparator i bankfilen."""

    thousands_separator: str = "."
    """Tusindtalsseparator der skal fjernes fra beløb og saldo."""

    encoding: str = "utf-8"
    """Tegnsæt i bankfilen."""

    skip_rows: int = 0
    """Antal rækker (efter eventuel header) der springes over (metadata-linjer etc.)."""

    delimiter: str = ";"
    """Kolonneseparator i bankfilen."""

    auto_detect: bool = True
    """Forsøg automatisk format-detektion ved import (clevercsv + heuristik + LLM-fallback).

    Når ``True`` ignoreres de øvrige felter og erstattes af det auto-detekterede format.
    Nyttigt hvis banken skifter eksportformat uden varsel.
    """


class Settings(BaseModel):
    """Firmakonfiguration – læses fra settings.yaml i firma-repoets rod."""

    company_name: str = Field(..., min_length=1)
    cvr: str = Field(..., pattern=r"^\d{8}$")
    first_year: int = Field(..., ge=1900, le=2100)
    month_start: int = Field(default=1, ge=1, le=12)
    vat_period_length: Literal["Q", "H", "Y"] = "Q"
    currency: str = Field(default="DKK", min_length=3, max_length=3)
    bank_csv_format: BankCsvFormat = Field(default_factory=BankCsvFormat)
    bank_download_format: BankDownloadFormat = Field(default_factory=BankDownloadFormat)
    invoice_template: str = "default"
    llm_model: str = "gpt-4o-mini"

    @field_validator("currency")
    @classmethod
    def currency_uppercase(cls, v: str) -> str:
        """Konverter valutakode til store bogstaver."""
        return v.upper()

    @field_validator("cvr", mode="before")
    @classmethod
    def cvr_strip(cls, v: str) -> str:
        """Fjern whitespace fra CVR."""
        return v.strip()
