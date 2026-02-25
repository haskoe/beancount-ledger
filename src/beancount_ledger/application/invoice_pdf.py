"""Generer faktura-PDF fra Invoice-objekt og Jinja2 HTML-skabelon (T-25).

Bruges af sales_service.generate_sales.
"""

from __future__ import annotations

import datetime
import importlib.resources
from decimal import Decimal
from pathlib import Path

import weasyprint
from jinja2 import Environment, FunctionLoader

from beancount_ledger.domain.customers import Customer
from beancount_ledger.domain.sales import Invoice
from beancount_ledger.domain.services import ServiceCatalog
from beancount_ledger.domain.settings import Settings

VAT_RATE = Decimal("0.25")

# ---------------------------------------------------------------------------
# Intern datastructur til skabelon-rendering
# ---------------------------------------------------------------------------


class _InvoiceLineContext:
    """Én fakturalinje til skabelon-rendering."""

    __slots__ = ("name", "quantity", "unit", "unit_price", "line_total", "has_vat")

    def __init__(
        self,
        name: str,
        quantity: Decimal,
        unit: str,
        unit_price: Decimal,
        line_total: Decimal,
        has_vat: bool,
    ) -> None:
        self.name = name
        self.quantity = quantity
        self.unit = unit
        self.unit_price = _fmt(unit_price)
        self.line_total = _fmt(line_total)
        self.has_vat = has_vat


# ---------------------------------------------------------------------------
# Hjælpefunktioner
# ---------------------------------------------------------------------------


def _fmt(amount: Decimal) -> str:
    """Formater beløb med 2 decimaler og tusindtalsseparator."""
    return f"{amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _load_template(template_name: str) -> str:
    """Indlæs HTML-skabelon fra infrastructure/templates/."""
    if template_name == "default":
        filename = "invoice_default.html"
    else:
        filename = template_name if template_name.endswith(".html") else f"{template_name}.html"

    templates_pkg = importlib.resources.files("beancount_ledger.infrastructure.templates")
    return (templates_pkg / filename).read_text(encoding="utf-8")


def _jinja_env(template_name: str) -> Environment:
    def loader(name: str) -> str | None:
        return _load_template(name)

    env = Environment(loader=FunctionLoader(loader), autoescape=True)
    return env


# ---------------------------------------------------------------------------
# Offentlig API
# ---------------------------------------------------------------------------


def generate_invoice_pdf(
    invoice: Invoice,
    customer: Customer,
    catalog: ServiceCatalog,
    settings: Settings,
    out_path: Path,
) -> Path:
    """Generer faktura-PDF og gem til *out_path*.

    Args:
        invoice:  Faktura-domænobjekt.
        customer: Kundeobjekt (BR-S01: valideret inden kald).
        catalog:  Ydelseskatalog (BR-S02: valideret inden kald).
        settings: Firma-indstillinger (company_name, cvr).
        out_path: Destination for PDF-filen.

    Returns:
        Stien til den skrevne PDF-fil.
    """
    # Beregn linjer og totaler (BR-S03–S05)
    line_contexts: list[_InvoiceLineContext] = []
    total_excl_vat = Decimal("0")
    vat_amount = Decimal("0")

    for line in invoice.lines:
        service = catalog.by_id(line.service_id)
        if service is None:
            raise ValueError(f"Ukendt service_id: {line.service_id!r}")
        unit_price = line.effective_price(service.standard_price)
        lt = line.line_total(service.standard_price)
        total_excl_vat += lt
        if service.vat_applicable:
            vat_amount += (lt * VAT_RATE).quantize(Decimal("0.01"))
        line_contexts.append(
            _InvoiceLineContext(
                name=service.name,
                quantity=line.quantity,
                unit=service.unit,
                unit_price=unit_price,
                line_total=lt,
                has_vat=service.vat_applicable,
            )
        )

    total_incl_vat = total_excl_vat + vat_amount
    due_date = invoice.invoice_date + datetime.timedelta(days=customer.payment_days)

    template_name = invoice.template if invoice.template else "default"
    env = _jinja_env(template_name)
    tmpl = env.get_template(template_name)

    html_str = tmpl.render(
        invoice_number=invoice.invoice_number,
        invoice_date=invoice.invoice_date.isoformat(),
        due_date=due_date.isoformat(),
        company_name=settings.company_name,
        cvr=settings.cvr,
        customer_name=customer.name,
        customer_cvr=customer.cvr,
        customer_email=customer.email,
        lines=line_contexts,
        total_excl_vat=_fmt(total_excl_vat),
        vat_amount=_fmt(vat_amount),
        total_incl_vat=_fmt(total_incl_vat),
        bank_account="(indsæt kontonummer)",
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    weasyprint.HTML(string=html_str).write_pdf(str(out_path))
    return out_path
