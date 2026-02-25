"""Domænemodeller for banktransaktioner (data/<YYYY>/bank.csv).

Svarende til spec afsnit 4.8.
Kolonnenavne og datoformat konfigureres i Settings.bank_csv_format.
"""

from __future__ import annotations

import csv
from curses import raw
import datetime
from decimal import Decimal
from pathlib import Path

from pydantic import BaseModel, Field

from beancount_ledger.domain.settings import BankCsvFormat


class BankTransaction(BaseModel):
    """Én banktransaktion fra bank.csv."""

    date: datetime.date
    description: str
    amount: Decimal
    balance: Decimal

    def transaction_id(self) -> str:
        """Returnér transaction ID (BR-B01)."""
        return f"bank;{self.date};{self.description};{self.amount}"


class BankFile(BaseModel):
    """Samling af banktransaktioner, indlæst fra bank.csv."""

    transactions: list[BankTransaction] = Field(default_factory=list)

    @classmethod
    def from_csv(
        cls,
        path: Path,
        fmt: BankCsvFormat | None = None,
    ) -> BankFile:
        """Indlæs bankfil fra CSV med konfigureret format.

        Bruger Settings.bank_csv_format-standarder hvis `fmt` ikke er angivet.
        """
        if fmt is None:
            fmt = BankCsvFormat()

        dec_sep = fmt.decimal_separator
        rows: list[BankTransaction] = []

        with path.open(encoding=fmt.encoding, newline="") as fh:
            reader = csv.DictReader(fh, delimiter=";")
            for raw in reader:
                raw_date = raw[fmt.date_column].strip()
                raw_amount = raw[fmt.amount_column].strip()
                raw_balance = raw[fmt.balance_column].strip()
                raw_desc = raw[fmt.description_column].strip()

                parsed_date = datetime.datetime.strptime(raw_date, fmt.date_format).date()

                # Normalisér decimaltegn → punkt for Decimal
                if dec_sep == ",":
                    raw_amount = raw_amount.replace(".", "").replace(",", ".")
                    raw_balance = raw_balance.replace(".", "").replace(",", ".")

                print(raw_amount)
                rows.append(
                    BankTransaction(
                        date=parsed_date,
                        description=raw_desc,
                        amount=Decimal(raw_amount),
                        balance=Decimal(raw_balance),
                    )
                )
        return cls(transactions=rows)
