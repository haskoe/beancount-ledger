"""Application service: generer lønposteringer fra loen.yaml (T-26).

Workflow (BR-L01–L03):
    1. Indlæs loen.yaml og audit.yaml.
    2. For hver lønkørsel:
       a. Valider net_salary (BR-L01 – håndhæves af SalaryRun-modellen).
       b. Byg BeancountTransaction med flag fra audit-status (* hvis godkendt, ! ellers).
       c. Opret AuditEntry med status "draft" kun for NYE kørsler.
    3. Skriv alle posteringer til generated/loen<ÅÅÅÅ>.beancount (overskriv).
    4. Gem audit.yaml.
    5. Commit "salary updated".

Beancount-filen regenereres hvert kørsel så korrektioner i loen.yaml altid slår igennem.
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
from beancount_ledger.domain.salary import SalaryFile, SalaryRun
from beancount_ledger.infrastructure import git_io
from beancount_ledger.infrastructure.beancount_writer import (
    write_transactions,
)
from beancount_ledger.infrastructure.yaml_io import load_yaml


def generate_salary(app_context: AppContext) -> int:
    audit = app_context.audit
    salary = app_context.salary

    for run in salary.runs:
        if not app_context.is_new(run.transaction_id()):
            continue

        flag = "!"
        txn = _build_transaction(run, flag=flag)
        app_context.add_transaction(TransactionType.SALARY, txn)

        entry = AuditEntry(
            transaction_id=run.transaction_id(),
            status="draft",
            type="salary",
            account="Liabilities:SalaryPayable",
            date=run.run_date,
            total_amount=run.gross_salary,
            vat_amount=Decimal("0"),
            vat_free_amount=Decimal("0"),
            receipt="",
        )
        audit.add(entry)
        
    return

# ---------------------------------------------------------------------------
# Interne hjælpefunktioner
# ---------------------------------------------------------------------------


def _build_transaction(run: SalaryRun, flag: str = "!") -> BeancountTransaction:
    """Byg beancount-postering for én lønkørsel (BR-L02).

    Posteringsstruktur:
        Expenses:Salary              gross_salary
        Liabilities:SalaryPayable   -net_salary
        Liabilities:TaxPayable      -tax
        Liabilities:ATPPayable      -atp_employer   ; arbejdsgiver ATP
        Expenses:ATP                 atp_employer
    """
    link = run.transaction_id().replace(";", "-")
    return BeancountTransaction(
        date=run.run_date,
        flag=flag,
        narration=f"Løn – {run.name} – {run.period}",
        links=[link],
        postings=[
            BeancountPosting(account="Expenses:Salary", amount=run.gross_salary),
            BeancountPosting(account="Liabilities:SalaryPayable", amount=-run.net_salary),
            BeancountPosting(account="Liabilities:TaxPayable", amount=-run.tax),
            BeancountPosting(
                account="Liabilities:ATPPayable",
                amount=-run.atp_employer,
                comment="arbejdsgiver ATP",
            ),
            BeancountPosting(account="Expenses:ATP", amount=run.atp_employer),
        ],
    )
