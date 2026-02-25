"""Application service: generer bankposteringer fra bank.csv (T-28).

Workflow:
    1. Indlæs bank.csv (BankFile).
    2. Behandl ALLE transaktioner (regenerer hel fil).
    3. Kendte transaktioner: hent konto fra audit, flag fra audit-status.
    4. Nye transaktioner: klassificér modkonto (navntilkonto → keywords → LLM).
    5. Skriv alle posteringer til generated/bank<YYYY>.beancount (overskriv).
    6. Tilføj audit-entries for NYE transaktioner.
    7. Gem audit.yaml og commit.

Kontering:
    Udgift (negativt beløb):  Debit modkonto  + Kredit bank-konto
    Indkomst (positivt beløb): Debit bank-konto + Kredit modkonto
"""

from __future__ import annotations

import re
from decimal import Decimal
from pathlib import Path

import yaml

from beancount_ledger.application.app_context import AppContext
from beancount_ledger.domain.audit import AuditEntry, AuditFile
from beancount_ledger.domain.bank import BankFile, BankTransaction
from beancount_ledger.domain.beancount_types import BeancountPosting, BeancountTransaction
from beancount_ledger.domain.chart_of_accounts import ChartOfAccounts
from beancount_ledger.domain.settings import Settings
from beancount_ledger.infrastructure import git_io
from beancount_ledger.infrastructure.beancount_writer import (
    write_transactions,
)
from beancount_ledger.infrastructure.yaml_io import load_yaml

# ---------------------------------------------------------------------------
# Konstanter
# ---------------------------------------------------------------------------

_BANK_ACCOUNT = "Assets:DK:8310:Bank:Erhverv"
_UNKNOWN_ACCOUNT = "Expenses:DK:7199:Unknown"


# ---------------------------------------------------------------------------
# Offentlig API
# ---------------------------------------------------------------------------


def generate_bank(app_context: AppContext) -> int:
    bank_file = BankFile.from_csv(app_context.bank_csv)
    if not bank_file.transactions:
        return 0

    audit = AuditFile.from_yaml(firm_layout.audit_yaml(root))
    rules = _load_keyword_rules(root)

    # Indlæs kontoplan til LLM-fallback (BR-B02)
    coa_path = firm_layout.chart_of_accounts_csv(root)
    if coa_path.exists():
        coa = ChartOfAccounts.from_csv(coa_path)
    else:
        coa = ChartOfAccounts.from_builtin()
    account_names = [a.beancount_account for a in coa.accounts]

    name_rules = _load_name_rules(root)

    out_path = firm_layout.bank_beancount(root, year)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    transactions: list[BeancountTransaction] = []
    new_count = 0

    for txn in bank_file.transactions:
        existing = audit.by_transaction_id(txn.transaction_id())

        if existing is not None and existing.status == "approved":
            # Godkendt af bruger – respektér gemt konto, brug ikke klassificering
            contra_account = existing.account
            flag = "*"
        elif existing is not None:
            # Draft: re-kør navntilkonto for at fange ny/rettet mapping.
            # Falder tilbage på gemt konto hvis ingen match.
            contra_account = (
                _classify_by_name(txn.description, name_rules, coa)
                or existing.account
            )
            flag = "!"
            if contra_account != existing.account:
                existing.account = contra_account
        else:
            # Ny transaktion: klassificér modkonto
            contra_account = (
                _classify_by_name(txn.description, name_rules, coa)
                or _classify(txn.description, rules)
            )
            if contra_account == _UNKNOWN_ACCOUNT and settings.llm_model:
                contra_account = _llm_fallback(
                    txn, account_names, settings.llm_model
                ) or _UNKNOWN_ACCOUNT
            flag = "!"
            audit.entries.append(
                AuditEntry(
                    transaction_id=txn.transaction_id(),
                    status="draft",
                    type="bank",
                    account=contra_account,
                    date=txn.date,
                    total_amount=abs(txn.amount),
                    vat_amount=Decimal("0"),
                    vat_free_amount=Decimal("0"),
                )
            )
            new_count += 1

        transactions.append(_build_transaction(txn, contra_account, flag=flag))

    if not transactions:
        return 0

    write_transactions(out_path, transactions, title=f"Bank {year}")
    audit.to_yaml(firm_layout.audit_yaml(root))
    git_io.commit_all(root, f"bank updated {year}")
    return new_count


# ---------------------------------------------------------------------------
# Keyword-klassificering (BR-B02)
# ---------------------------------------------------------------------------


def _load_name_rules(root: Path) -> list[tuple[str, str]]:
    """Indlæs navntilkonto.csv og returnér liste af (keyword, konto-suffix) tupler.

    Lookup og merge-rækkefølge:
      1. Bundlet skabelon i app-pakken           – base
      2. ``<parent>/navntilkonto.csv``            – overstyrér/udvider base
      3. ``<firma-rod>/navntilkonto.csv``         – overstyrér/udvider parent

    Alle niveauer merges: firma-niveau keywords vinder over parent over template.
    """
    def _parse(text: str) -> dict[str, str]:
        result: dict[str, str] = {}
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith(";"):
                continue
            parts = line.split(";")
            if len(parts) >= 2 and parts[0].strip() and parts[1].strip():
                result[parts[0].strip().lower()] = parts[1].strip()
        return result

    # 1. Bundlet template som base
    import importlib.resources as ir
    merged: dict[str, str] = {}
    pkg = ir.files("beancount_ledger.infrastructure.templates")
    try:
        merged.update(_parse((pkg / "navntilkonto.csv").read_text(encoding="utf-8")))
    except FileNotFoundError:
        pass

    # 2. Parent-niveau (gælder alle firmaer under base_dir)
    shared = navntilkonto_csv_shared(root.parent)
    if shared.exists():
        merged.update(_parse(shared.read_text(encoding="utf-8")))

    # 3. Firma-niveau override
    firm_path = navntilkonto_csv(root)
    if firm_path.exists():
        merged.update(_parse(firm_path.read_text(encoding="utf-8")))

    # Bevar original case på keyword fra merged (vi opbevarede lowercase-nøgler)
    # Brug normalized keywords direkte, da _classify_by_name sammenligner lowercase
    return list(merged.items())


def _resolve_suffix(suffix: str, coa: ChartOfAccounts) -> str | None:
    """Find den fulde beancount-konto hvis sidste segment matcher *suffix*."""
    for account in coa.accounts:
        if account.beancount_account.split(":")[-1] == suffix:
            return account.beancount_account
    return None


def _classify_by_name(
    description: str,
    name_rules: list[tuple[str, str]],
    coa: ChartOfAccounts,
) -> str | None:
    """Returnér beancount-konto via navntilkonto.csv-opslag, eller None ved ingen match.

    Matcher keyword (case-insensitiv) mod beskrivelse.
    Kolonne 2-værdien bruges som:
    - Fuldt kontonavn hvis den indeholder ':' → bruges direkte
    - Suffix → slås op i kontoplanen via _resolve_suffix
    """
    desc_lower = description.lower()
    for keyword, account_or_suffix in name_rules:
        if keyword.lower() in desc_lower:
            if ":" in account_or_suffix:
                return account_or_suffix  # fuld konto direkte
            return _resolve_suffix(account_or_suffix, coa)
    return None


def _load_keyword_rules(root: Path) -> list[dict]:
    """Indlæs keyword-regler fra bank_keywords.yaml.

    Falder tilbage på den bundlede skabelon hvis filen ikke findes i firma-repoet.
    """
    local = firm_layout.bank_keywords_yaml(root)
    if local.exists():
        data = yaml.safe_load(local.read_text(encoding="utf-8"))
    else:
        import importlib.resources as ir
        pkg = ir.files("beancount_ledger.infrastructure.templates")
        data = yaml.safe_load((pkg / "bank_keywords.yaml").read_bytes().decode("utf-8"))
    return data.get("rules", []) if data else []


def _classify(description: str, rules: list[dict]) -> str:
    """Returnér beancount-konto for *description* via keyword-matching.

    Afprøver reglerne i rækkefølge – første match vinder.
    Returnerer ``_UNKNOWN_ACCOUNT`` hvis ingen regel matcher.
    """
    desc_lower = description.lower()
    for rule in rules:
        for keyword in rule.get("keywords", []):
            if keyword.lower() in desc_lower:
                return rule["account"]
    return _UNKNOWN_ACCOUNT


def _llm_fallback(
    txn: BankTransaction,
    account_names: list[str],
    llm_model: str,
) -> str | None:
    """Brug LLM til at foreslå konto når keyword-matching fejler (BR-B02)."""
    from beancount_ledger.application import llm_client  # noqa: PLC0415 (lazy import)

    return llm_client.suggest_account(
        description=txn.description,
        amount=txn.amount,
        txn_date=txn.date,
        accounts=account_names,
        llm_model=llm_model,
    )


# ---------------------------------------------------------------------------
# Beancount-posteringsbygger
# ---------------------------------------------------------------------------


def _build_transaction(txn: BankTransaction, contra_account: str, flag: str = "!") -> BeancountTransaction:
    """Byg en BeancountTransaction for én banktransaktion.

    Udgift (negativt beløb):   Debit modkonto,  Kredit bank-konto
    Indkomst (positivt beløb): Debit bank-konto, Kredit modkonto
    """
    amount = txn.amount

    if amount < Decimal("0"):
        # Udgift
        postings = [
            BeancountPosting(account=contra_account, amount=-amount),
            BeancountPosting(account=_BANK_ACCOUNT, amount=amount),
        ]
    else:
        # Indkomst
        postings = [
            BeancountPosting(account=_BANK_ACCOUNT, amount=amount),
            BeancountPosting(account=contra_account, amount=-amount),
        ]

    # Rens beskrivelse: fjern backslashes og ekstra whitespace
    narration = re.sub(r"\s+", " ", txn.description.replace("\\", " ")).strip()

    return BeancountTransaction(
        date=txn.date,
        flag=flag,
        narration=narration,
        tags=["bank"],
        metadata={"balance": str(txn.balance)},
        postings=postings,
    )
