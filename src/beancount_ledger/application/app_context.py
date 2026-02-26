from dataclasses import dataclass
from pathlib import Path
from functools import cached_property
from datetime import datetime
import importlib.resources

from beancount_ledger.domain.settings import Settings
from beancount_ledger.domain.current import CurrentState
from beancount_ledger.util import date_util, vat_util
from beancount_ledger.infrastructure import git_io

from beancount_ledger.domain.audit import AuditEntry, AuditFile
from beancount_ledger.domain.customers import Customer, CustomerRegister
from beancount_ledger.domain.sales import Invoice, SalesFile
from beancount_ledger.domain.services import ServiceCatalog

# ---------------------------------------------------------------------------
# (skabelonfilnavn, destinationsfilnavn i data/<YYYY>/, render_year)
# ---------------------------------------------------------------------------
_YEAR_TEMPLATES: list[tuple[str, str, bool]] = [
    ("salg.yaml", "salg.yaml", True),
    ("loen.yaml", "loen.yaml", True),
    ("udbytte.yaml", "udbytte.yaml", True),
    ("bank.csv", "bank.csv", False),
]

@dataclass
class AppContext:
    """Indkapsler Settings og CurrentState med utility funktioner"""

    root_path: Path
    settings: Settings
    current_state: CurrentState

    def __post_init__(self):
        if not self.settings or not self.settings.start_date:
            return

        if not self.current_state.current_year:
            self.current_state.current_year = self.settings.start_date.year
            self.current_state.current_vat_period = vat_util.get_vat_period_for_date(self.settings.start_date, self.settings.vat_period_length)
            self.current_state.to_yaml(self.current_yaml)  # Gem opdateret
            init_year(self)
        

    @cached_property
    def data_dir(self) -> Path:
        return self.root_path / "data"

    def get_next_invoice_number(self) -> Path:
        return f"{self.current_state.next_invoice_number:0>4}"    

    def increment_next_invoice_number(self) -> Path:
        self.current_state.next_invoice_number += 1
        self.current_state.to_yaml(self.current_yaml)
        return self.current_state.next_invoice_number

    def get_invoice_path(self, invoice: Invoice) -> Path:
        return self.generated_dir / "invoices" / f"faktura-{invoice.customer_id}-{invoice.invoice_number}.pdf"

    def get_year_dir(self, year: int) -> Path:
        return self.data_dir / str(year)

    @cached_property
    def year_dir(self) -> Path:
        return self.get_year_dir(str(self.current_state.current_year))

    @cached_property
    def generated_dir(self) -> Path:
        """Returnér generated/ mappen."""
        return self.root_path / "generated"

    @cached_property
    def invoices_dir(self) -> Path:
        """Returnér generated/invoices/ mappen."""
        return self.generated_dir / "invoices"

    @cached_property
    def bank_download_dir(self) -> Path:
        return self.data_dir / "bankcsv-download"

    @cached_property
    def receipts_dir(self) -> Path:
        """Returnér receipts/ mappen."""
        return self.root_path / "receipts"

    @cached_property
    def receipts_intray_dir(self) -> Path:
        """Returnér receipts-intray/ mappen."""
        return self.root_path / "receipts-intray"

    @cached_property
    def settings_yaml(self) -> Path:
        return self.root_path / "settings.yaml"

    @cached_property
    def current_yaml(self) -> Path:
        return self.root_path / "current.yaml"

    @cached_property
    def primo_csv(self) -> Path:
        return self.root_path / "primo.csv"

    @cached_property
    def navntilkonto_csv(self) -> Path:
        return self.root_path / "navntilkonto.csv"

    @cached_property
    def primo_beancount(self) -> Path:
        return self.generated_dir / "primo.beancount"
    
    def sales_beancount(self) -> Path:
        return self.generated_dir / f"salg{self.current_state.current_year}.beancount"
    

    @cached_property
    def primo_date(self) -> datetime.date:
        return date_util.add_days(self.settings.start_date, -1)

    @cached_property
    def customers(self) -> CustomerRegister:
        return CustomerRegister.from_yaml(self.root_path / "sales_accounts.yaml")

    @cached_property
    def catalog(self) -> ServiceCatalog:
        return ServiceCatalog.from_yaml(self.root_path / "ydelser.yaml")

    @cached_property
    def sales(self) -> SalesFile:
        return SalesFile.from_yaml(self.year_dir / "salg.yaml")

    @cached_property
    def audit_yaml(self) -> Path:
        return self.year_dir / "audit.yaml"

    def get_audit(self) -> AuditFile:
        return AuditFile.from_yaml(self.audit_yaml)
    
    def commit_all(self, message: str) -> None:
        """Commit alle ændringer i root repo med given commit-besked."""
        git_io.commit_all(self.root_path, message)

def init_year(app_context: AppContext) -> bool:
    current_year = app_context.current_state.current_year
    year_path = app_context.get_year_dir(current_year)

    substitutions = {"year": str(current_year)}
    templates_pkg = importlib.resources.files("beancount_ledger.infrastructure.templates")

    for template_name, dest_name, render in _YEAR_TEMPLATES:
        dest = year_path / dest_name
        content = (templates_pkg / template_name).read_text(encoding="utf-8")
        if render:
            for key, value in substitutions.items():
                content = content.replace("{" + key + "}", value)
        dest.write_text(content, encoding="utf-8")

    app_context.commit_all(f"year {current_year} created")
    return True
