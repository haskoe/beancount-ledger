
from datetime import date
from enum import Enum

valid_vat_periods = ("H1", "H2", "Q1", "Q2", "Q3", "Q4")

def assert_valid_vat_period(vat_period: str) -> bool:
    assert vat_period is not None, "VAT-periode må ikke være None"
    assert vat_period in valid_vat_periods

def get_vat_period_for_date(d: date, vat_period_length: str) -> str:
    month = d.month
    if vat_period_length == "H":
        return f"H{1 if month <= 6 else 2}"
    else:
        quarter = (month - 1) // 3 + 1
        return f"Q{quarter}"
   