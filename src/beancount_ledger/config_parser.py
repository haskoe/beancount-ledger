import yaml
from pathlib import Path
from typing import List, Optional, Union
from datetime import date
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict

class CompanyMetadata(BaseModel):
    name: str
    cvr: str
    fiscal_year_start: date
    historical_fiscal_years: List[date] = []
    vat_period: str  # e.g., "quarterly", "monthly", "yearly"

class PricePoint(BaseModel):
    account_name: str
    price_type: str
    price: Decimal
    start_date: date
    end_date: Optional[date] = None

class CompanyConfig(BaseModel):
    metadata: CompanyMetadata
    prices: List[PricePoint] = []

class AccountMapping(BaseModel):
    external_id: str  # Key used in internal logic or CSVs
    beancount_account: str
    default_parent: Optional[str] = None
    regex: Optional[str] = None

class AccountConfig(BaseModel):
    accounts: List[AccountMapping]

def load_yaml(file_path: Union[str, Path]) -> dict:
    """Helper to load a YAML file."""
    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def load_company_config(file_path: Union[str, Path]) -> CompanyConfig:
    """Loads company metadata and prices from a YAML file."""
    data = load_yaml(file_path)
    return CompanyConfig.model_validate(data)

def load_account_mapping(file_path: Union[str, Path]) -> AccountConfig:
    """Loads account mappings from a YAML file."""
    data = load_yaml(file_path)
    if isinstance(data, list):
        return AccountConfig(accounts=data)
    return AccountConfig.model_validate(data)
