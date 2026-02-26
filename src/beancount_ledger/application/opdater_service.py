"""Application service: orkestrerer opdatering af alle posteringstyper (T-30).

Kaldrækkefølge:
    0. auto_import_bank_download – transformér download-CSV til bank.csv hvis til stede
    1. generate_sales     (T-24)
    2. generate_salary    (T-26)
    3. generate_dividends (T-27)
    4. generate_bank      (T-28)

Returnerer en dict med antal nye posteringer pr. type.
"""

from __future__ import annotations

from pathlib import Path

# from beancount_ledger.application.bank_import_service import auto_import_bank_download
from beancount_ledger.application.app_context import AppContext
from beancount_ledger.application.bank_service import generate_bank
from beancount_ledger.application.dividend_service import generate_dividends
from beancount_ledger.application.salary_service import generate_salary
from beancount_ledger.application.sales_service import generate_sales


def opdater(app_context: AppContext) -> dict[str, int]:
    results: dict[str, int] = {
        "salg": 0,
        "loen": 0,
        "udbytte": 0,
        "bank": 0,
    }

    # Transformér evt. download-CSV til bank.csv inden videre behandling
    # auto_import_bank_download(root, year)

    results["salg"] = generate_sales(app_context=app_context)
    results["loen"] = generate_salary(app_context=app_context)
    results["udbytte"] = generate_dividends(app_context=app_context)
    #results["bank"] = generate_bank(app_context=app_context)

    return results
