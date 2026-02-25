"""CSV I/O til bank.csv og standardkontoplan.csv.

Bruges af application-laget.
Alle stier skal bruge pathlib.Path (BR-03).
"""

from __future__ import annotations

import csv
from pathlib import Path

from beancount_ledger.domain.settings import BankCsvFormat


def load_csv(path: Path, config: BankCsvFormat) -> list[dict[str, str]]:
    """Indlæs bank-CSV og returnér liste af rå dict-rækker (streng-værdier).

    Kolonnenavne og tegnsæt bestemmes af `config` (Settings.bank_csv_format).
    Antager semikolon-separator (matcher bank-template).
    """
    rows: list[dict[str, str]] = []
    with path.open(encoding=config.encoding, newline="") as fh:
        reader = csv.DictReader(fh, delimiter=";")
        for row in reader:
            rows.append(dict(row))
    return rows


def load_chart_of_accounts(path: Path) -> list[dict[str, str]]:
    """Indlæs standardkontoplan.csv (semikolon-separeret) og returnér liste af rå dict-rækker.

    Forventede kolonner: id;beancount_account;description;default_vat
    """
    rows: list[dict[str, str]] = []
    with path.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh, delimiter=";")
        for row in reader:
            rows.append({k: v.strip() for k, v in row.items()})
    return rows
