# AGENTS.md

This document provides essential information for AI agents working in this codebase.

## Project Overview

This is a **Danish accounting system** built on top of [Beancount](https://github.com/beancount/beancount), a double-entry accounting system.

### Key Features

- **CSV-based data import** for bank transactions, sales, payroll, and other financial data
- **Jinja2 templating** for generating Beancount entries
- **YAML configuration** for company-specific settings
- **Beancount Query Language (BQL)** for querying ledger data
- **Modular command structure** with subcommands for different operations

### Target Audience

This system is designed for Danish companies and accountants, with support for:
- Danish tax regulations
- VAT (moms) calculations
- Danish bank formats
- Danish date formats (dd-mm-YYYY)

## Essential Commands

### Build and Run

```bash
# Install dependencies using uv
uv sync

# Run the application
python -m beancount_ledger

# Show help
python -m beancount_ledger --help

# Run specific commands
python -m beancount_ledger opdater --help
python -m beancount_ledger afstem --help
python -m beancount_ledger godkend --help
python -m beancount_ledger status --help
python -m beancount_ledger moms_luk --help
```

### Development Commands

```bash
# Format code
uv run ruff format

# Lint code
uv run ruff check

# Type check
uv run mypy
```

## Code Organization and Structure

### Directory Structure

```
src/beancount_ledger/
├── __init__.py
├── __main__.py              # Main entry point
├── constants.py            # CSV column names and formats
├── context.py              # LedgerContext for shared state
├── handlers/
│   ├── __init__.py
│   ├── afstem.py           # Reconciliation handler
│   ├── godkend.py           # Approval handler
│   ├── moms_luk.py         # VAT closing handler
│   ├── opdater.py           # Update handler
│   └── status.py           # Status handler
├── models/
│   ├── __init__.py
│   ├── config.py           # Configuration models
│   ├── transaction.py      # Transaction data structures
│   └── types.py            # Type definitions
├── queries/
│   ├── __init__.py
│   └── query.py           # BQL query execution
└── utils/
    ├── __init__.py
    ├── csv.py              # CSV parsing utilities
    └── dates.py            # Date handling utilities
```

### Main Entry Point

The `main.py` file serves as the entry point and dispatches to handlers based on subcommands:
- `opdater` - Update transactions
- `afstem` - Reconcile accounts
- `godkend` - Approve transactions
- `status` - Show status
- `moms_luk` - Close VAT period

## Naming Conventions and Style Patterns

### Python Style

- **Type hints**: Required throughout the codebase
- **Docstrings**: Google style format
- **Variable naming**: snake_case for variables and functions
- **Class naming**: PascalCase for classes
- **Constants**: UPPER_SNAKE_CASE in `constants.py`

### Key Patterns

1. **Context Object Pattern**: `LedgerContext` class holds shared state
2. **Dataclass Usage**: Extensive use of `@dataclass` for data structures
3. **Pydantic Validation**: Configuration validation using Pydantic models
4. **Template Rendering**: Jinja2 templates for generating Beancount entries
5. **CSV Parsing**: Pandas-based CSV parsing with validation

## Testing Approach and Patterns

### Test Structure

Tests are located in the `tests/` directory and follow the structure:

```
tests/
├── test_handlers/
│   ├── test_afstem.py
│   ├── test_godkend.py
│   ├── test_moms_luk.py
│   ├── test_opdater.py
│   └── test_status.py
├── test_models/
│   ├── test_config.py
│   ├── test_transaction.py
│   └── test_types.py
└── test_utils/
    ├── test_csv.py
    └── test_dates.py
```

### Test Patterns

- **Unit tests**: Test individual functions and methods
- **Integration tests**: Test handler workflows
- **Mocking**: Use `unittest.mock` for external dependencies
- **Assertions**: Use `pytest` assertions

### Running Tests

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_handlers/test_opdater.py

# Run with coverage
uv run pytest --cov=src/beancount_ledger
```

## CSV File Formats and Specifications

The system uses CSV files for data import. Column names are defined in `constants.py`:

### Bank Transactions

```python
BANK_TRANSACTION_COLUMNS = [
    "dato",           # Date (dd-mm-YYYY)
    "beløb",         # Amount
    "modtagers konto", # Account number
    "modtager",       # Payee
    "kode",           # Transaction code
    "reference",      # Reference
    "tekst",          # Description
]
```

### Sales Invoices

```python
SALES_INVOICE_COLUMNS = [
    "dato",           # Date (dd-mm-YYYY)
    "fakturanummer",  # Invoice number
    "kundenummer",   # Customer number
    "kundenavn",     # Customer name
    "beløb",         # Amount
    "moms",          # VAT amount
    "tekst",          # Description
]
```

### Purchase Invoices

```python
PURCHASE_INVOICE_COLUMNS = [
    "dato",           # Date (dd-mm-YYYY)
    "fakturanummer",  # Invoice number
    "leverandør",     # Supplier
    "beløb",         # Amount
    "moms",          # VAT amount
    "konto",         # Account
    "tekst",          # Description
]
```

### Payroll

```python
PAYROLL_COLUMNS = [
    "dato",           # Date (dd-mm-YYYY)
    "ansat",         # Employee
    "beløb",         # Amount
    "type",          # Payroll type
    "tekst",          # Description
]
```

## Configuration Structure

### YAML Configuration

The system uses YAML files for configuration with Pydantic validation:

```yaml
# firma/config.yaml

firma:
  navn: "Company Name"
  cvr: "12345678"
  valuta: "DKK"
  startdato: "01-01-2023"
  
accounts:
  bank:
    - "Assets:Bank:Company Bank Account"
  income:
    - "Income:Sales"
  expenses:
    - "Expenses:Supplies"
  
defaults:
  moms_konto: "Liabilities:Taxes:VAT"
  moms_sats: 25  # Danish VAT rate
```

### Configuration Model

```python
# models/config.py

class FirmaConfig(BaseModel):
    navn: str
    cvr: str
    valuta: str = "DKK"
    startdato: str
    accounts: dict[str, list[str]]
    defaults: dict[str, Any] = {}
```

## Template System

### Jinja2 Templates

The system uses Jinja2 templates to generate Beancount entries. Templates are located in the `templates/` directory:

```
templates/
├── bank_transaction.j2
├── sales_invoice.j2
├── purchase_invoice.j2
└── payroll.j2
```

### Template Variables

Common template variables:
- `transaction`: The transaction data
- `config`: The company configuration
- `context`: The ledger context
- `date`: The current date

### Example Template

```jinja2
# templates/bank_transaction.j2

{{ date }} * {{ transaction.tekst }}
{{ transaction.beløb }} {{ transaction.konto }}
{{ transaction.beløb }} Expenses:Unknown
```

## Date and Decimal Handling

### Date Format

- **Input format**: `dd-mm-YYYY` (Danish standard)
- **Internal format**: Python `datetime.date` objects
- **Output format**: `YYYY-MM-DD` (Beancount standard)

### Date Utilities

```python
# utils/dates.py

def parse_danish_date(date_str: str) -> date:
    """Parse Danish date format (dd-mm-YYYY)"""
    return datetime.strptime(date_str, "%d-%m-%Y").date()

def format_beancount_date(date_obj: date) -> str:
    """Format date for Beancount (YYYY-MM-DD)"""
    return date_obj.strftime("%Y-%m-%d")
```

### Decimal Handling

- **Locale**: Danish (dk_DK.UTF-8)
- **Decimal separator**: `.` (period)
- **Thousands separator**: ` ` (space)

```python
# Example: 1.234,56 becomes 1234.56

def parse_danish_decimal(amount_str: str) -> Decimal:
    """Parse Danish decimal format"""
    return Decimal(amount_str.replace(" ", "").replace(",", "."))
```

## Beancount Query Language Usage

### BQL Queries

The system uses Beancount Query Language (BQL) for querying ledger data:

```python
# queries/query.py

def run_bql_query(ledger: Ledger, query: str) -> list[dict]:
    """Execute a BQL query"""
    results = []
    for row in ledger.query(query):
        results.append(dict(row._asdict()))
    return results
```

### Common Queries

```python
# Get unapproved transactions
"SELECT * FROM transactions WHERE approved = False"

# Get transactions by date range
"SELECT * FROM transactions WHERE date >= '2023-01-01' AND date <= '2023-12-31'"

# Get balance by account
"SELECT sum(amount) FROM transactions GROUP BY account"
```

## Important Gotchas and Non-Obvious Patterns

### 1. Date Format Mismatches

- **Input**: `dd-mm-YYYY` (Danish)
- **Internal**: `datetime.date` objects
- **Output**: `YYYY-MM-DD` (Beancount)

Always use the utility functions for date conversion.

### 2. Decimal Parsing

Danish decimals use `.` as separator but may have spaces for thousands:
- `1 234,56` should be parsed as `1234.56`

### 3. CSV Validation

CSV files are validated against column names in `constants.py`. If columns don't match, the system will raise an error.

### 4. Account Naming

Beancount accounts must follow specific naming conventions:
- Use colons to separate hierarchy: `Assets:Bank:Account`
- Avoid special characters
- Be consistent with capitalization

### 5. VAT (Moms) Handling

Danish VAT has specific rules:
- Standard rate: 25%
- Reduced rate: 12%
- VAT is calculated separately from the base amount

### 6. Transaction Approval

Transactions go through a workflow:
1. Imported (unapproved)
2. Reconciled (afstem)
3. Approved (godkend)
4. Finalized

## Project-Specific Context

### Danish Accounting Regulations

This system is designed for Danish accounting and tax regulations:
- VAT (moms) calculations
- Danish bank formats
- Danish date formats
- Danish currency (DKK)

### Beancount Integration

The system integrates with Beancount for:
- Double-entry accounting
- Transaction tracking
- Reporting
- Querying

### Fava Integration

[Fava](https://github.com/beancount/fava) is used as the web interface for:
- Viewing transactions
- Generating reports
- Managing the ledger

## Additional Resources

- [Beancount Documentation](https://docs.beancount.org/)
- [Beancount Query Language](https://docs.beancount.org/tutorial_query_language.html)
- [Fava Documentation](https://beancount.github.io/fava/)
- [Jinja2 Documentation](https://jinja.palletsprojects.com/)
