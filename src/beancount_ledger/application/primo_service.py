"""Application service: generer primo.beancount fra primo.csv (T-23).

Workflow:
    1. Indlæs primo.csv (domain.PrimoFile).
    2. Kontrollér at balancen er 0 (is_balanced).
    3. Byg én BeancountTransaction pr. primo-entry.
    4. Sørg for at primo.beancount-headeren eksisterer.
    5. Append alle posteringer til generated/primo.beancount.
    6. Commit "primo updated".

Generer kun poster der ikke allerede er i filen (idempotent via overwrite-strategi:
primo.beancount overskrives, da primoposteringer aldrig ændrer antal — kun data).
"""

from __future__ import annotations

from pathlib import Path
from datetime import date

from beancount_ledger.application.app_context import AppContext
from beancount_ledger.domain.beancount_types import BeancountPosting, BeancountTransaction
from beancount_ledger.domain.primo import PrimoEntry, PrimoFile
from beancount_ledger.infrastructure import company_layout, git_io
from beancount_ledger.infrastructure.beancount_writer import (
    append_transactions,
    ensure_beancount_header,
)


class PrimoBalanceError(Exception):
    """Kastes hvis primo-posteringerne ikke balancerer."""


def generate_primo(app_context: AppContext) -> int:
    primo_path = app_context.primo_csv
    if not primo_path.exists():
        raise FileNotFoundError(f"primo.csv ikke fundet: {primo_path}")

    primo = PrimoFile.from_csv(primo_path)

    if not primo.is_balanced():
        total = sum(e.amount for e in primo.entries)
        raise PrimoBalanceError(
            f"Primo-posteringerne summerer til {total}, ikke 0. "
            "Ret beløbene i primo.csv så de balancerer."
        )

    transactions = [_to_transaction(entry, app_context.primo_date) for entry in primo.entries]

    out_path = company_layout.primo_beancount(app_context.root_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Primo overskrives altid (indholdet ændrer sig ved redit af primo.csv)
    out_path.write_text("", encoding="utf-8")
    ensure_beancount_header(out_path, "Primobalance")
    append_transactions(out_path, transactions)

    git_io.commit_all(app_context.root_path, "primo updated")
    return len(transactions)


def _to_transaction(entry: PrimoEntry, primo_date: date) -> BeancountTransaction:
    narration = f"Primo {entry.beancount_account}"

    return BeancountTransaction(
        date=primo_date,
        narration=narration,
        tags=["primo"],
        postings=[
            BeancountPosting(account=entry.beancount_account, amount=entry.amount),
            BeancountPosting(account="Equity:Opening-Balances"),  # auto-balance
        ],
    )
