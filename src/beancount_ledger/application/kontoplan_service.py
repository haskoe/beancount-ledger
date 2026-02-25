"""Application service: generer kontoplan.beancount fra standardkontoplan.csv.

Kaldes ved alle kommandoer (primo, opdater, import-bank osv.) så
kontoplan.beancount altid afspejler den aktuelle standardkontoplan.csv.
Filen overskrives altid — den er autogenereret og må ikke redigeres manuelt.
"""

from __future__ import annotations

import csv
from pathlib import Path

from beancount_ledger.infrastructure import company_layout


def generate_kontoplan(root: Path) -> int:
    """Generer (eller regenerer) kontoplan.beancount fra standardkontoplan.csv.

    Læser ``standardkontoplan.csv`` via DictReader (springer header over),
    skriver én ``1900-01-01 open <konto> DKK``-linje pr. konto og
    **overskriver** altid den eksisterende kontoplan.beancount.

    Args:
        root: Firma-repoets rod.

    Returns:
        Antal ``open``-direktiver skrevet (0 hvis CSV ikke findes).
    """
    source = company_layout.chart_of_accounts_csv(root)
    if not source.exists():
        return 0

    lines: list[str] = ["; Autogenereret fra standardkontoplan.csv – redigér ikke manuelt.\n"]
    count = 0
    with source.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh, delimiter=";")
        for row in reader:
            account = row.get("beancount_account", "").strip()
            if account:
                lines.append(f"1900-01-01 open {account} DKK\n")
                count += 1

    dest = company_layout.kontoplan_beancount(root)
    dest.write_text("".join(lines), encoding="utf-8")
    return count
