"""LLM-klient til bankmatching (T-29).

Understøtter to backends afhængigt af ``llm_model``-indstillingen:

* **llama-server (lokal)** – ``llm_model`` starter med ``"llamaserver:"`` eller ``"llama-server:"``
  – f.eks. ``"llama-server:http://localhost:8080"`` eller ``"llamaserver:http://localhost:8080"``.
  – Kræver at llama-server kører lokalt og eksponerer ``/v1/chat/completions``.

* **OpenAI**              – alle andre modelnavn (f.eks. ``"gpt-4o-mini"``).
  – Kræver at ``OPENAI_API_KEY`` er sat i miljøet.

Offentlig API
-------------
match_receipt(...)   → str | None
    Returnerer filnavn på det bilag der bedst matcher en banktransaktion,
    eller ``None`` hvis intet matcher.

suggest_account(...) → str | None
    Returnerer et kontonavn fra chart_of_accounts, eller ``None``.
"""

from __future__ import annotations

import logging
import requests
from datetime import date
from decimal import Decimal

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Offentlig API
# ---------------------------------------------------------------------------


def match_receipt(
    bank_description: str,
    bank_amount: Decimal,
    bank_date: date,
    receipt_texts: dict[str, str],
    llm_model: str,
) -> str | None:
    """Find det bilag der bedst matcher en banktransaktion.

    Args:
        bank_description: Beskrivelsestekst fra bankfilen.
        bank_amount:      Beløb (negativt = udgift).
        bank_date:        Transaktionsdato.
        receipt_texts:    Mapping filnavn → indhold (kun .txt-filer).
        llm_model:        Modelnavn (se modulkommentar).

    Returns:
        Filnavn (nøgle i receipt_texts) eller None.
    """
    if not receipt_texts:
        return None

    entries_text = ""
    for fname, text in receipt_texts.items():
        # Begræns hvert bilag til 600 tegn for at holde prompt-størrelsen nede
        entries_text += f"\n--- {fname} ---\n{text[:600].strip()}\n"

    prompt = (
        f"A bank transaction has the following data:\n"
        f"  Date:        {bank_date.isoformat()}\n"
        f"  Description: {bank_description}\n"
        f"  Amount:      {bank_amount} DKK\n\n"
        f"The following receipt/invoice files are available:{entries_text}\n"
        f"Which receipt file best matches this bank transaction?\n"
        f"Rules:\n"
        f"- Match by vendor name, amount, and approximate date.\n"
        f"- Reply with ONLY the exact filename (e.g. 'telmore_50900_250102.txt').\n"
        f"- Reply with 'none' if no receipt is a reasonable match.\n"
        f"No explanation, no punctuation — just the filename or 'none'."
    )

    try:
        response = _chat(llm_model, prompt).strip().lower()
    except Exception as exc:  # noqa: BLE001
        log.warning("LLM-kald fejlede under receipt-matching: %s", exc)
        return None

    # Valider: svaret skal præcist matche ét af filnavnene
    for fname in receipt_texts:
        if fname.lower() == response:
            return fname
        # Løs match: svar indeholder filnavnet eller omvendt
        if fname.lower() in response or response in fname.lower():
            return fname

    return None


def suggest_account(
    description: str,
    amount: Decimal,
    txn_date: date,
    accounts: list[str],
    llm_model: str,
) -> str | None:
    """Brug LLM til at foreslå en beancount-konto.

    Args:
        description: Beskrivelsestekst (bank + evt. bilagstekst).
        amount:      Transaktionsbeløb.
        txn_date:    Transaktionsdato.
        accounts:    Liste af gyldige beancount-konti fra standardkontoplan.
        llm_model:   Modelnavn.

    Returns:
        Kontonavn fra *accounts*, eller None.
    """
    if not accounts:
        return None

    # Begræns kontolisten til 150 poster for at holde prompt nede
    accounts_text = "\n".join(accounts[:150])

    prompt = (
        f"A bank transaction:\n"
        f"  Date:        {txn_date.isoformat()}\n"
        f"  Description: {description}\n"
        f"  Amount:      {amount} DKK\n\n"
        f"Choose the single best matching account from the list below:\n"
        f"{accounts_text}\n\n"
        f"Reply with ONLY the exact account name from the list above.\n"
        f"No explanation, no punctuation."
    )

    try:
        response = _chat(llm_model, prompt).strip()
    except Exception as exc:  # noqa: BLE001
        log.warning("LLM-kald fejlede under account-suggestion: %s", exc)
        return None

    # Eksakt match først
    for account in accounts:
        if account == response:
            return account
    # Løs match: svar er prefix af kontonavn eller omvendt
    for account in accounts:
        if response and (account.startswith(response) or response.startswith(account)):
            return account

    return None


def detect_csv_format(sample_rows: list[list[str]], delimiter: str, llm_model: str) -> dict | None:
    """Brug LLM til at detektere kolonnemapping i en bank-CSV.

    Args:
        sample_rows: De første (typisk 3-5) datarækker fra filen.
        delimiter:   Den detekterede kolonneseparator.
        llm_model:   Modelnavn.

    Returns:
        Dict med nøgler svarende til ``BankDownloadFormat``-felter, eller None.
    """
    import json  # noqa: PLC0415

    rows_text = ""
    for i, row in enumerate(sample_rows[:5]):
        rows_text += f"Række {i}: {delimiter.join(row)}\n"

    prompt = (
        "De følgende rækker er fra en dansk bank-CSV-eksport:\n"
        f"{rows_text}\n"
        "Identificér kolonnemapping og format. Svar KUN med et JSON-objekt – ingen forklaring:\n"
        '{"date_col": 0, "text_col": 2, "amount_col": 3, "balance_col": 4, '
        '"has_header": false, "date_format": "%d-%m-%Y", '
        '"decimal_separator": ",", "thousands_separator": ".", '
        f'"delimiter": ";", "encoding": "utf-8"}}\n'
        "Kolonner er 0-indekseret. Brug Python strftime-format for date_format."
    )

    try:
        raw = _chat(llm_model, prompt, max_tokens=200).strip()
    except Exception as exc:  # noqa: BLE001
        log.warning("LLM-kald fejlede under CSV-format-detektion: %s", exc)
        return None

    # Udtræk JSON fra svaret (LLM kan tilføje tekst rundt om)
    start = raw.find("{")
    end = raw.rfind("}") + 1
    if start == -1 or end == 0:
        log.warning("LLM returnerede ikke gyldigt JSON under format-detektion: %r", raw[:200])
        return None
    try:
        return json.loads(raw[start:end])
    except json.JSONDecodeError as exc:
        log.warning("JSON-parsefejl under format-detektion: %s – raw: %r", exc, raw[:200])
        return None


# ---------------------------------------------------------------------------
# Interne hjælpere
# ---------------------------------------------------------------------------


def _chat(llm_model: str, prompt: str, max_tokens: int = 80) -> str:
    """Kald LLM-backend og returnér svartekst."""
    if llm_model.startswith("llamaserver:"):
        endpoint = llm_model[len("llamaserver:"):]
        return _llamaserver_chat(endpoint, prompt, max_tokens=max_tokens)
    if llm_model.startswith("llama-server:"):
        endpoint = llm_model[len("llama-server:"):]
        return _llamaserver_chat(endpoint, prompt, max_tokens=max_tokens)
    return _openai_chat(llm_model, prompt, max_tokens=max_tokens)


def _llamaserver_chat(endpoint: str, prompt: str, max_tokens: int = 80) -> str:
    """Kald lokal llama-server via /v1/chat/completions."""
    url = f"{endpoint.rstrip('/')}/v1/chat/completions"
    payload = {
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.0,
        "max_tokens": max_tokens,
        "stream": False,
    }
    response = requests.post(url, json=payload, timeout=120)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


def _openai_chat(model: str, prompt: str, max_tokens: int = 80) -> str:
    """Kald OpenAI Chat Completions API."""
    import openai  # noqa: PLC0415  (lazy import – valgfri afhængighed)

    client = openai.OpenAI()
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=0.0,
    )
    return response.choices[0].message.content or ""
