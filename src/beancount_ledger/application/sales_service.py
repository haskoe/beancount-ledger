"""Application service: generer salgsposteringer fra salg.yaml (T-24).

Workflow (BR-S01–S07):
    1. Indlæs salg.yaml, sales_accounts.yaml og ydelser.yaml.
    2. For hver faktura:
       a. Valider customer_id (BR-S01) og service_id'er (BR-S02).
       b. Beregn totaler (BR-S03–S05).
       c. Generer faktura-PDF kun for NYE fakturaer (BR-S06).
       d. Byg BeancountTransaction med flag '!' (draft) eller '*' (godkendt fra audit).
    3. Skriv alle posteringer til salg<ÅÅÅÅ>.beancount (overskriv).
    4. Tilføj audit-entries for NYE fakturaer.
    5. Gem audit.yaml.
    6. Commit "sales updated".

Beancount-filen regenereres hvert kørsel så korrektioner i salg.yaml altid slår
igennem. Allerede kendte fakturaer bibeholder deres flag fra audit-status.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from beancount_ledger.application.app_context import AppContext
from beancount_ledger.domain.customers import Customer, CustomerRegister
from beancount_ledger.domain.sales import Invoice, SalesFile
from beancount_ledger.domain.services import ServiceCatalog
from beancount_ledger.application.invoice_pdf import generate_invoice_pdf
from beancount_ledger.domain.audit import AuditEntry, AuditFile
from beancount_ledger.domain.beancount_types import BeancountPosting, BeancountTransaction
from beancount_ledger.infrastructure import git_io
from beancount_ledger.infrastructure.beancount_writer import (
    write_transactions,
)
from beancount_ledger.infrastructure.yaml_io import load_yaml

VAT_RATE = Decimal("0.25")

# Debitor-samlekonto (posteringen på modstående side af debitor)
_AR_ACCOUNT = "Assets:DK:DebitorOmkostninger"
_VAT_ACCOUNT = "Liabilities:DK:9500:Moms:Udgående"


class SalesValidationError(Exception):
    """Fejl ved validering af salgsdata (BR-S01–S02)."""


def generate_sales(app_context: AppContext) -> int:
    settings = app_context.settings
    customers = app_context.customers
    catalog = app_context.catalog
    audit = app_context.get_audit()
    sales = app_context.sales

    # --- Behandl alle fakturaer → regenerer hel fil ---
    out_path = app_context.sales_beancount()

    transactions: list[BeancountTransaction] = []
    new_count = 0

    for invoice in sales.invoices:
        # BR-S01: valider kunde
        customer = customers.by_id(invoice.customer_id)
        if customer is None:
            raise SalesValidationError(
                f"ukendt customer_id={invoice.customer_id!r}"
            )

        # BR-S02: valider ydelser
        for line in invoice.lines:
            if catalog.by_id(line.service_id) is None:
                raise SalesValidationError(
                    f"Faktura {invoice.invoice_number}: "
                    f"ukendt service_id={line.service_id!r}"
                )

        # BR-S03–S05: beregn totaler
        total_excl, vat, total_incl = _calculate_totals(invoice, catalog)

        # Bestem flag fra audit-status
        invoice.invoice_number = app_context.get_next_invoice_number()
        existing = audit.by_transaction_id(invoice.transaction_id())
        flag = "*" if (existing and existing.status == "godkendt") else "!"

        # BR-S06: generer faktura-PDF og opret audit-entry kun for NYE fakturaer
        if existing is None:
            pdf_path = app_context.get_invoice_path(invoice)
            generate_invoice_pdf(invoice, customer, catalog, settings, pdf_path)
            relative_pdf = pdf_path.relative_to(app_context.root_path).as_posix()
            entry = AuditEntry(
                transaction_id=invoice.transaction_id(),
                status="draft",
                type="sales",
                account=customer.beancount_account,
                date=invoice.invoice_date,
                total_amount=total_incl,
                vat_amount=vat,
                vat_free_amount=Decimal("0"),
                receipt=relative_pdf,
            )
            audit.add(entry)
            new_count += 1

        # Byg Beancount-postering
        txn = _build_transaction(invoice, customer, catalog, total_excl, vat, flag=flag)
        transactions.append(txn)

    if not transactions:
        return 0

    write_transactions(out_path, transactions, title=f"Salg {app_context.current_state.current_year}")
    audit.to_yaml(app_context.audit_yaml)
    app_context.commit_all("sales updated")
    return new_count


# ---------------------------------------------------------------------------
# Interne hjælpefunktioner
# ---------------------------------------------------------------------------


def _calculate_totals(
    invoice: Invoice, catalog: ServiceCatalog
) -> tuple[Decimal, Decimal, Decimal]:
    """Returnér (total_ekskl_moms, moms, total_inkl_moms) for en faktura."""
    total_excl = Decimal("0")
    vat = Decimal("0")
    for line in invoice.lines:
        service = catalog.by_id(line.service_id)
        assert service is not None  # allerede valideret
        lt = line.line_total(service.standard_price)
        total_excl += lt
        if service.vat_applicable:
            vat += (lt * VAT_RATE).quantize(Decimal("0.01"))
    total_incl = total_excl + vat
    return total_excl, vat, total_incl


def _build_transaction(
    invoice: Invoice,
    customer: Customer,
    catalog: ServiceCatalog,
    total_excl: Decimal,
    vat: Decimal,
    flag: str = "!",
) -> BeancountTransaction:
    """Byg en BeancountTransaction for en salgsfaktura."""
    total_incl = total_excl + vat
    # Opbyg kreditlinjer pr. ydelse (grupperet på income_account)
    income_by_account: dict[str, Decimal] = {}
    for line in invoice.lines:
        service = catalog.by_id(line.service_id)
        assert service is not None
        lt = line.line_total(service.standard_price)
        income_by_account[service.income_account] = (
            income_by_account.get(service.income_account, Decimal("0")) + lt
        )

    postings: list[BeancountPosting] = [
        # Debet: Debitor
        BeancountPosting(account=customer.beancount_account, amount=total_incl),
    ]
    # Kredit: Salgsindtægt pr. konto
    for acc, amt in income_by_account.items():
        postings.append(BeancountPosting(account=acc, amount=-amt))

    if vat > Decimal("0"):
        postings.append(BeancountPosting(account=_VAT_ACCOUNT, amount=-vat))

    return BeancountTransaction(
        date=invoice.invoice_date,
        flag=flag,
        narration=f"Faktura {invoice.invoice_number}",
        links=[invoice.invoice_number.replace(" ", "_")],
        tags=["salg"],
        postings=postings,
    )
