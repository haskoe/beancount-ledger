"""Application service: generer udbytteposteringer fra udbytte.yaml (T-27).

Workflow (BR-U01–U03):
    1. Indlæs udbytte.yaml og audit.yaml.
    2. For hver udbytteudbetaling:
       a. Valider net_amount (BR-U01 – håndhæves af DividendPayment-modellen).
       b. Byg BeancountTransaction med flag fra audit-status (* hvis godkendt, ! ellers).
       c. Opret AuditEntry kun for NYE udbetalinger.
    3. Skriv alle posteringer til generated/udbytte<ÅÅÅÅ>.beancount (overskriv).
    4. Gem audit.yaml.
    5. Commit "dividends updated".

Beancount-filen regenereres hvert kørsel så korrektioner i udbytte.yaml altid slår igennem.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from beancount_ledger.transaction import TransactionType
from beancount_ledger.application.app_context import AppContext
from beancount_ledger.domain.audit import AuditEntry, AuditFile
from beancount_ledger.domain.beancount_types import (
    BeancountPosting,
    BeancountTransaction,
)
from beancount_ledger.domain.dividends import DividendPayment, DividendsFile
from beancount_ledger.infrastructure import git_io
from beancount_ledger.infrastructure.beancount_writer import (
    write_transactions,
)


def generate_dividends(app_context: AppContext) -> int:
    audit = app_context.audit
    dividends = app_context.dividends

    for payment in dividends.payments:
        if not app_context.is_new(payment.transaction_id()):
            continue

        txn = _build_transaction(payment, flag="!")
        app_context.add_transaction(TransactionType.DIVIDEND, txn)

        entry = AuditEntry(
            transaction_id=payment.transaction_id(),
            status="draft",
            type="dividend",
            account="Liabilities:DividendPayable",
            date=payment.run_date,
            total_amount=payment.gross_amount,
            vat_amount=Decimal("0"),
            vat_free_amount=Decimal("0"),
            receipt="",
        )
        audit.add(entry)
    return


# ---------------------------------------------------------------------------
# Interne hjælpefunktioner
# ---------------------------------------------------------------------------

MINUS1 = Decimal("-1.00")  # BR-U02

def _build_transaction(payment: DividendPayment, flag: str = "!") -> BeancountTransaction:
    """Byg beancount-postering for én udbytteudbetaling (BR-U02/U03).

    Posteringsstruktur:
        Equity:RetainedEarnings          gross_amount
        Liabilities:DividendPayable     -net_amount
        Liabilities:WithholdingTaxPayable  -withholding_tax
    """
    link = payment.transaction_id().replace(";", "-")
    return BeancountTransaction(
        date=payment.run_date,
        flag=flag,
        narration=f"Udbytte – {payment.name}",
        links=[link],
        postings=[
            BeancountPosting(account="Equity:RetainedEarnings", amount=payment.gross_amount),
            BeancountPosting(
                account="Liabilities:DividendPayable",
                amount=-payment.net_amount,
            ),
            BeancountPosting(
                account="Liabilities:WithholdingTaxPayable",
                amount=MINUS1 * payment.withholding_tax,
                comment="kildeskat 27%",
            ),
        ],
    )
