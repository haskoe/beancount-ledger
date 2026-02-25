from dataclasses import dataclass
from pathlib import Path
from functools import cached_property
from datetime import datetime

from beancount_ledger.domain.settings import Settings
from beancount_ledger.domain.current import CurrentState
from beancount_ledger.application.init_year import init_year
from beancount_ledger.util import date_util

@dataclass
class AppContext:
    """Indkapsler Settings og CurrentState med utility funktioner"""

    root_path: Path
    settings: Settings
    current_state: CurrentState

    def __post_init__(self):
        if not self.settings or not self.settings.start_date:
            return
        
        init_year(self.root_path, self.get_data_dir(self.settings.start_date.year), self.settings.start_date.year)

    @cached_property
    def data_dir(self) -> Path:
        return self.root_path / "data"

    def get_year_dir(self, year: int) -> Path:
        return self.data_dir / str(year)

    @cached_property
    def year_dir(self) -> Path:
        return self.get_data_dir(str(self.current_state.current_year))

    @cached_property
    def generated_dir(self) -> Path:
        """Returnér generated/ mappen."""
        return self.root_path / "generated"

    @cached_property
    def invoices_dir(self) -> Path:
        """Returnér generated/invoices/ mappen."""
        return self.generated_dir / "invoices"

    @cached_property
    def receipts_dir(self) -> Path:
        """Returnér receipts/ mappen."""
        return self.root_path / "receipts"

    @cached_property
    def receipts_intray_dir(self) -> Path:
        """Returnér receipts-intray/ mappen."""
        return self.root_path / "receipts-intray"

    @cached_property
    def primo_csv(self) -> Path:
        return self.root_path / "primo.csv"

    @cached_property
    def primo_beancount(self) -> Path:
        return self.generated_dir / "primo.beancount"

    @cached_property
    def primo_date(self) -> datetime.date:
        return date_util.add_days(self.settings.start_date, -1)
