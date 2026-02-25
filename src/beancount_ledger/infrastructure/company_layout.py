"""Firma-repo stieResolution (BR-03: brug altid pathlib.Path).

Alle stifunktioner tager `root: Path` som første argument —
repoets rod svarer direkte til firma-roden (ingen CVR-nesting).

Mappe-layout:
    <root>/
        settings.yaml
        primo.csv
        sales_accounts.yaml
        standardkontoplan.csv
        ydelser.yaml
        current.yaml
        data/
            <YYYY>/
                salg.yaml
                loen.yaml
                udbytte.yaml
                bank.csv
        generated/
            audit.yaml
            current.yaml          ← alternativt ved root
            salg<YYYY>.beancount
            loen<YYYY>.beancount
            udbytte<YYYY>.beancount
            <YYYY>.beancount      ← bank/udgifter
            primo.beancount
            invoices/
                invoice-<nr>.pdf
        receipts/
        receipts-intray/
"""

from __future__ import annotations

from pathlib import Path

# ---------------------------------------------------------------------------
# Rodmapper
# ---------------------------------------------------------------------------


def data_dir(root: Path, year: int) -> Path:
    """Returnér data/<YYYY>/ mappen."""
    return root / "data" / str(year)


def generated_dir(root: Path) -> Path:
    """Returnér generated/ mappen."""
    return root / "generated"


def invoices_dir(root: Path) -> Path:
    """Returnér generated/invoices/ mappen."""
    return generated_dir(root) / "invoices"


def receipts_dir(root: Path) -> Path:
    """Returnér receipts/ mappen."""
    return root / "receipts"


def receipts_intray_dir(root: Path) -> Path:
    """Returnér receipts-intray/ mappen."""
    return root / "receipts-intray"


# ---------------------------------------------------------------------------
# Konfigurationsfiler (firma-rodet)
# ---------------------------------------------------------------------------


def settings_yaml(root: Path) -> Path:
    return root / "settings.yaml"


def primo_yaml(root: Path) -> Path:
    return root / "primo.csv"


def sales_accounts_yaml(root: Path) -> Path:
    return root / "sales_accounts.yaml"


def chart_of_accounts_csv(root: Path) -> Path:
    return root / "standardkontoplan.csv"


def ydelser_yaml(root: Path) -> Path:
    return root / "ydelser.yaml"


def bank_keywords_yaml(root: Path) -> Path:
    """Returnér bank_keywords.yaml i firma-repoets rod."""
    return root / "bank_keywords.yaml"


def navntilkonto_csv(root: Path) -> Path:
    """Returnér navntilkonto.csv i firma-repoets rod (firma-niveau override)."""
    return root / "navntilkonto.csv"


def navntilkonto_csv_shared(base_dir: Path) -> Path:
    """Returnér navntilkonto.csv i forældremappen (delt på tværs af firmaer)."""
    return base_dir / "navntilkonto.csv"


def current_yaml(root: Path) -> Path:
    return root / "current.yaml"


# ---------------------------------------------------------------------------
# Års-datafiler (data/<YYYY>/)
# ---------------------------------------------------------------------------


def sales_yaml(root: Path, year: int) -> Path:
    return data_dir(root, year) / "salg.yaml"


def salary_yaml(root: Path, year: int) -> Path:
    return data_dir(root, year) / "loen.yaml"


def dividends_yaml(root: Path, year: int) -> Path:
    return data_dir(root, year) / "udbytte.yaml"


def bank_csv(root: Path, year: int) -> Path:
    return data_dir(root, year) / "bank.csv"


def bank_download_dir(root: Path, year: int) -> Path:
    """Returnér data/<YYYY>/bankcsv-download/ mappen til rå bankeksporter."""
    return data_dir(root, year) / "bankcsv-download"


# ---------------------------------------------------------------------------
# Genererede beancount-filer (generated/)
# ---------------------------------------------------------------------------


def regnskab_beancount(root: Path) -> Path:
    """Returnér regnskab.beancount i firma-repoets rod."""
    return root / "regnskab.beancount"


def kontoplan_beancount(root: Path) -> Path:
    """Returnér kontoplan.beancount i firma-repoets rod."""
    return root / "kontoplan.beancount"


def audit_yaml(root: Path) -> Path:
    return generated_dir(root) / "audit.yaml"


def primo_beancount(root: Path) -> Path:
    return generated_dir(root) / "primo.beancount"


def sales_beancount(root: Path, year: int) -> Path:
    return generated_dir(root) / f"salg{year}.beancount"


def salary_beancount(root: Path, year: int) -> Path:
    return generated_dir(root) / f"loen{year}.beancount"


def dividends_beancount(root: Path, year: int) -> Path:
    return generated_dir(root) / f"udbytte{year}.beancount"


def bank_beancount(root: Path, year: int) -> Path:
    """Beancount-fil til bankposteringer og udgifter for et givet år."""
    return generated_dir(root) / f"bank{year}.beancount"


def invoice_pdf(root: Path, invoice_number: str) -> Path:
    return invoices_dir(root) / f"invoice-{invoice_number}.pdf"


# ---------------------------------------------------------------------------
# Hjælpefunktioner
# ---------------------------------------------------------------------------


def ensure_dirs(root: Path, year: int) -> None:
    """Opret alle standard-mapper under `root` for `year`."""
    for d in (
        data_dir(root, year),
        bank_download_dir(root, year),
        generated_dir(root),
        invoices_dir(root),
        receipts_dir(root),
        receipts_intray_dir(root),
    ):
        d.mkdir(parents=True, exist_ok=True)


def all_beancount_files(root: Path, year: int) -> list[Path]:
    """Returnér alle beancount-filer for et givet år (kan bruges til fava include-liste)."""
    return [
        primo_beancount(root),
        sales_beancount(root, year),
        salary_beancount(root, year),
        dividends_beancount(root, year),
        bank_beancount(root, year),
    ]


def latest_year(root: Path) -> int | None:
    """Returnér det seneste år der findes i data/-mappen, eller None."""
    base = root / "data"
    if not base.is_dir():
        return None
    years = [int(d.name) for d in base.iterdir() if d.is_dir() and d.name.isdigit()]
    return max(years) if years else None
