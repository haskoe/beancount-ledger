"""Application service: importér og transformér bank-download-CSV (T-28 forløber).

Workflow:
    1. Kopiér den råe bankfil til data/<YYYY>/bankcsv-download/.
    2. Læs filen iht. BankDownloadFormat (kolonneindeks, header-flag etc.).
    3. Filtrer rækker hvor dato tilhører <YYYY>.
    4. Skriv transformeret data til data/<YYYY>/bank.csv (header + rækker).
    5. Commit med "bank csv imported".

Eksisterende bank.csv overskrives (import er idempotent – kør igen ved ny
eksport fra banken).
"""

from __future__ import annotations

import csv
import datetime
import io
import logging
import shutil
from pathlib import Path

log = logging.getLogger(__name__)

from beancount_ledger.application.app_context import AppContext
from beancount_ledger.application import llm_client as _llm
from beancount_ledger.domain.settings import BankDownloadFormat, Settings
from beancount_ledger.infrastructure import git_io
from beancount_ledger.infrastructure.yaml_io import load_yaml


# ---------------------------------------------------------------------------
# Internt målformat (header i bank.csv)
# ---------------------------------------------------------------------------
_TARGET_HEADER = ["Dato", "Tekst", "Beløb", "Saldo"]


def import_bank_csv(app_context: AppContext) -> int:
    return
    
    # download_dir = app_context.bank_download_dir
    # dest_raw = download_dir / source.name
    # shutil.copy2(source, dest_raw)

    # # Læs og transformér
    # rows = _read_and_transform(source, fmt, year)

    # if not rows:
    #     raise ValueError(
    #         f"Ingen rækker fundet for år {year} i {source.name}. "
    #         "Tjek at filen er eksporteret for det rigtige år."
    #     )

    # # Skriv til data/<YYYY>/bank.csv
    # target = firm_layout.bank_csv(root, year)
    # target.parent.mkdir(parents=True, exist_ok=True)
    # with target.open("w", encoding="utf-8", newline="") as fh:
    #     writer = csv.writer(fh, delimiter=";", quoting=csv.QUOTE_MINIMAL)
    #     writer.writerow(_TARGET_HEADER)
    #     writer.writerows(rows)

    # git_io.commit_all(root, f"bank csv imported {year}")
    # return len(rows)


def auto_import_bank_download(app_context: AppContext) -> int:
    download_dir = firm_layout.bank_download_dir(root, year)
    if not download_dir.is_dir():
        return 0

    files = sorted(download_dir.iterdir())
    if not files:
        return 0

    fmt = _load_download_format(root)
    all_rows: list[list[str]] = []
    processed: list[Path] = []

    llm_model: str | None = None
    if fmt.auto_detect:
        llm_model = _load_llm_model(root)

    for src in files:
        if not src.is_file():
            continue
        file_fmt = fmt
        if fmt.auto_detect:
            file_fmt = detect_bank_format(src, llm_model=llm_model)
            log.info("Auto-detekteret format for %s: %s", src.name, file_fmt.model_dump())
        rows = _read_and_transform(src, file_fmt, year)
        if rows:
            all_rows.extend(rows)
            processed.append(src)

    if not all_rows:
        return 0

    # Sortér efter dato (kolonneindeks 0, format DD-MM-YYYY)
    all_rows.sort(key=lambda r: datetime.datetime.strptime(r[0], "%d-%m-%Y"))

    target = firm_layout.bank_csv(root, year)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh, delimiter=";", quoting=csv.QUOTE_MINIMAL)
        writer.writerow(_TARGET_HEADER)
        writer.writerows(all_rows)

    for src in processed:
        src.unlink()

    return len(all_rows)


# ---------------------------------------------------------------------------
# Hjælpefunktioner
# ---------------------------------------------------------------------------


def _load_download_format(root: Path) -> BankDownloadFormat:
    """Indlæs BankDownloadFormat fra settings.yaml, eller brug standardværdier."""
    settings_path = firm_layout.settings_yaml(root)
    if not settings_path.exists():
        return BankDownloadFormat()
    data = load_yaml(settings_path)
    raw_fmt = data.get("bank_download_format", {})
    return BankDownloadFormat(**raw_fmt) if raw_fmt else BankDownloadFormat()


def _load_llm_model(root: Path) -> str:
    """Hent llm_model-indstillingen fra settings.yaml."""
    settings_path = firm_layout.settings_yaml(root)
    if not settings_path.exists():
        return "gpt-4o-mini"
    data = load_yaml(settings_path)
    return data.get("llm_model", "gpt-4o-mini")


def _normalise_number(raw: str, fmt: BankDownloadFormat) -> str:
    """Fjern tusindtalsseparator og returnér streng med komma som decimaltegn.

    Tusindtalsseparatoren fjernes K*UN* når den optræder mellem to cifre
    (f.eks. "1.026,75" → "1026,75") – ikke i tekst som "Aftalenr. 123".
    """
    import re
    stripped = raw.strip()
    if fmt.thousands_separator and fmt.thousands_separator != fmt.decimal_separator:
        sep = re.escape(fmt.thousands_separator)
        # Fjern kun separatoren når den er omgivet af cifre (look-behind + look-ahead)
        stripped = re.sub(rf"(?<=\d){sep}(?=\d)", "", stripped)
    # Normalisér altid til komma internt (target-format)
    if fmt.decimal_separator == ".":
        stripped = stripped.replace(".", ",")
    return stripped


def _read_and_transform(
    source: Path,
    fmt: BankDownloadFormat,
    year: int,
) -> list[list[str]]:
    """Læs råfil og returnér transformerede rækker filtreret til *year*."""
    rows: list[list[str]] = []

    with source.open(encoding=fmt.encoding, newline="") as fh:
        reader = csv.reader(fh, delimiter=fmt.delimiter)

        if fmt.has_header:
            next(reader, None)  # spring header over

        for _ in range(fmt.skip_rows):
            next(reader, None)

        for raw_row in reader:
            if not any(cell.strip() for cell in raw_row):
                continue  # tom linje

            try:
                date_str = raw_row[fmt.date_col].strip()
                date = datetime.datetime.strptime(date_str, fmt.date_format).date()
            except (IndexError, ValueError):
                continue  # spring over ugyldige rækker

            if date.year != year:
                continue

            text = raw_row[fmt.text_col].strip() if len(raw_row) > fmt.text_col else ""
            amount = (
                _normalise_number(raw_row[fmt.amount_col], fmt)
                if len(raw_row) > fmt.amount_col
                else ""
            )
            balance = (
                _normalise_number(raw_row[fmt.balance_col], fmt)
                if len(raw_row) > fmt.balance_col
                else ""
            )

            # Dato skrives altid på internt format DD-MM-YYYY
            rows.append([date.strftime("%d-%m-%Y"), text, amount, balance])

    return rows


# ---------------------------------------------------------------------------
# Auto-detektion af bankfilformat
# ---------------------------------------------------------------------------

_DATE_FORMATS = [
    ("%d-%m-%Y", r"\d{2}-\d{2}-\d{4}"),
    ("%Y-%m-%d", r"\d{4}-\d{2}-\d{2}"),
    ("%d/%m/%Y", r"\d{2}/\d{2}/\d{4}"),
    ("%d.%m.%Y", r"\d{2}\.\d{2}\.\d{4}"),
    ("%m/%d/%Y", r"\d{2}/\d{2}/\d{4}"),
]


def detect_bank_format(source: Path, llm_model: str | None = None) -> BankDownloadFormat:
    """Auto-detektér bankfilens format.

    Strategi (i prioriteret rækkefølge):

    1. **Encoding** – prøver UTF-8, UTF-8-BOM og Latin-1.
    2. **Dialect** – ``clevercsv`` detekterer delimiter og quoting-stil.
    3. **Kolonner** – heuristik baseret på dato-mønstre og talformat.
    4. **LLM-fallback** – hvis heuristikken fejler og ``llm_model`` er angivet.

    Args:
        source:    Stien til den downloadede bankfil.
        llm_model: LLM-modelnavn (se ``llm_client``). Bruges kun ved fallback.

    Returns:
        Et ``BankDownloadFormat``-objekt klar til brug i ``_read_and_transform``.
    """
    encoding = _detect_encoding(source)
    raw_text = source.read_text(encoding=encoding, errors="replace")

    delimiter, has_header = _detect_dialect(raw_text)

    sample_rows = _parse_sample(raw_text, delimiter, n=10)
    if not sample_rows:
        log.warning("detect_bank_format: ingen rækker fundet i %s", source.name)
        return BankDownloadFormat(delimiter=delimiter, encoding=encoding)

    data_rows = sample_rows[1:] if has_header else sample_rows

    fmt = _heuristic_columns(data_rows, delimiter, encoding, has_header)
    if fmt is not None:
        log.debug("detect_bank_format: heuristik lykkes for %s", source.name)
        return fmt

    if llm_model:
        log.debug("detect_bank_format: prøver LLM-fallback for %s", source.name)
        fmt = _llm_detect_format(sample_rows, delimiter, encoding, has_header, llm_model)
        if fmt is not None:
            return fmt

    log.warning(
        "detect_bank_format: kunne ikke bestemme format for %s – bruger standardværdier",
        source.name,
    )
    return BankDownloadFormat(delimiter=delimiter, encoding=encoding, has_header=has_header)


# -- Hjælpere til detect_bank_format ----------------------------------------


def _detect_encoding(source: Path) -> str:
    """Prøv UTF-8, UTF-8-BOM og Latin-1."""
    raw = source.read_bytes()[:8192]
    for enc in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            raw.decode(enc)
            return "utf-8" if enc == "utf-8-sig" else enc
        except UnicodeDecodeError:
            continue
    return "latin-1"


def _detect_dialect(raw_text: str) -> tuple[str, bool]:
    """Returner (delimiter, has_header) ved hjælp af clevercsv."""
    delimiter = ";"
    try:
        import clevercsv  # noqa: PLC0415

        dialect = clevercsv.Sniffer().sniff(raw_text, verbose=False)
        if dialect is not None and dialect.delimiter:
            delimiter = dialect.delimiter
    except Exception as exc:  # noqa: BLE001
        log.debug("clevercsv-sniffer fejlede: %s – falder tilbage til ';'", exc)

    # Undersøg om første række ligner en header
    lines = [ln for ln in raw_text.splitlines() if ln.strip()]
    if not lines:
        return delimiter, False
    first_row = next(csv.reader([lines[0]], delimiter=delimiter), [])
    has_header = _looks_like_header(first_row)
    return delimiter, has_header


def _parse_sample(raw_text: str, delimiter: str, n: int = 10) -> list[list[str]]:
    """Returnér op til *n* udfyldte rækker fra *raw_text*."""
    rows: list[list[str]] = []
    for row in csv.reader(io.StringIO(raw_text), delimiter=delimiter):
        if any(c.strip() for c in row):
            rows.append([c.strip().strip('"') for c in row])
        if len(rows) >= n:
            break
    return rows


def _looks_like_header(row: list[str]) -> bool:
    """Første række ligner en header hvis ingen celler er datoer eller tal."""
    for cell in row:
        s = cell.strip().strip('"')
        if not s:
            continue
        if _parse_date_cell(s) is not None:
            return False
        if _is_numeric_cell(s):
            return False
    # Noget ikke-tomt indhold → sandsynligvis header-labels
    return any(c.strip().strip('"') for c in row)


def _parse_date_cell(s: str) -> tuple[datetime.date, str] | None:
    """Forsøg at parse *s* som dato. Returnér (date, format) eller None."""
    for fmt_str, _ in _DATE_FORMATS:
        try:
            return datetime.datetime.strptime(s, fmt_str).date(), fmt_str
        except ValueError:
            continue
    return None


def _is_numeric_cell(s: str) -> bool:
    """Undersøg om *s* repræsenterer et tal (med eventuelt ,.+-tegn)."""
    import re  # noqa: PLC0415

    cleaned = re.sub(r"[\s]", "", s)
    # Fjern ét eventuelt fortegn
    cleaned = cleaned.lstrip("+-")
    if not cleaned:
        return False
    # Tillad cifre, komma og punktum
    if not re.fullmatch(r"[\d.,]+", cleaned):
        return False
    # Mindst ét ciffer
    return bool(re.search(r"\d", cleaned))


def _detect_number_format(cells: list[str]) -> tuple[str, str]:
    """Gæt decimal- og tusindepunktum fra *cells*.

    Returnér (decimal_separator, thousands_separator).
    Standardantagelse: decimal=',' og thousands='.'.
    """
    import re  # noqa: PLC0415

    dot_last = 0  # antal celler hvor '.' sidst
    comma_last = 0  # antal celler hvor ',' sidst

    for cell in cells:
        m = re.search(r"([,\.])(\d+)$", cell)
        if m:
            if m.group(1) == ",":
                comma_last += 1
            else:
                dot_last += 1

    if dot_last > comma_last:
        return ".", ","
    return ",", "."


def _heuristic_columns(
    data_rows: list[list[str]],
    delimiter: str,
    encoding: str,
    has_header: bool,
) -> BankDownloadFormat | None:
    """Forsøg at bestemme kolonneindeks via heuristik.

    Returnér et ``BankDownloadFormat`` eller None hvis vi ikke er sikre nok.
    """
    if not data_rows or not data_rows[0]:
        return None

    n_cols = max(len(r) for r in data_rows)

    # For hver kolonne: tæl dato-hits og tal-hits
    date_hits: dict[int, int] = {i: 0 for i in range(n_cols)}
    num_hits: dict[int, int] = {i: 0 for i in range(n_cols)}

    detected_date_fmt: str = "%d-%m-%Y"

    for row in data_rows:
        for i, cell in enumerate(row):
            if _parse_date_cell(cell) is not None:
                date_hits[i] += 1
                result = _parse_date_cell(cell)
                if result:
                    detected_date_fmt = result[1]
            elif _is_numeric_cell(cell):
                num_hits[i] += 1

    # date_col: kolonnen med flest dato-hits
    best_date_col = max(date_hits, key=lambda k: date_hits[k])
    if date_hits[best_date_col] == 0:
        log.debug("_heuristic_columns: ingen dato-kolonne fundet")
        return None

    # Numeriske kolonner
    numeric_cols = sorted(
        [i for i in range(n_cols) if num_hits[i] > 0 and i != best_date_col],
        key=lambda k: num_hits[k],
        reverse=True,
    )

    if len(numeric_cols) < 1:
        log.debug("_heuristic_columns: for få numeriske kolonner")
        return None

    # amount = numerisk kolonne med mindst absolutværdi (typisk)
    # balance = numerisk kolonne med størst absolutværdi (typisk)
    # Hvis kun én numerisk kolonne, brug den til amount
    amount_col = numeric_cols[0]
    balance_col = numeric_cols[1] if len(numeric_cols) >= 2 else numeric_cols[0]

    # text_col: den ikke-dato, ikke-numeriske kolonne – helst den længste streng
    other_cols = [
        i for i in range(n_cols) if i != best_date_col and i not in numeric_cols
    ]
    if other_cols:
        # Vælg den kolonne med den gennemsnitligt længste tekst
        text_col = max(
            other_cols,
            key=lambda i: sum(len(r[i]) for r in data_rows if i < len(r)) / len(data_rows),
        )
    else:
        # Ingen dedikeret tekstkolonne – brug kolonne 1 (gæt)
        text_col = 1 if n_cols > 1 else 0

    # Detektér talformat fra numeriske celler
    num_cells: list[str] = []
    for row in data_rows:
        for ci in numeric_cols:
            if ci < len(row) and row[ci]:
                num_cells.append(row[ci])

    decimal_sep, thousands_sep = _detect_number_format(num_cells)

    return BankDownloadFormat(
        has_header=has_header,
        date_col=best_date_col,
        text_col=text_col,
        amount_col=amount_col,
        balance_col=balance_col,
        date_format=detected_date_fmt,
        decimal_separator=decimal_sep,  # type: ignore[arg-type]
        thousands_separator=thousands_sep,
        encoding=encoding,
        delimiter=delimiter,
    )


def _llm_detect_format(
    sample_rows: list[list[str]],
    delimiter: str,
    encoding: str,
    has_header: bool,
    llm_model: str,
) -> BankDownloadFormat | None:
    """LLM-fallback: bed modellen identificere kolonnemapping."""
    raw = _llm.detect_csv_format(sample_rows, delimiter, llm_model)
    if raw is None:
        return None

    try:
        return BankDownloadFormat(
            has_header=raw.get("has_header", has_header),
            date_col=int(raw["date_col"]),
            text_col=int(raw["text_col"]),
            amount_col=int(raw["amount_col"]),
            balance_col=int(raw["balance_col"]),
            date_format=raw.get("date_format", "%d-%m-%Y"),
            decimal_separator=raw.get("decimal_separator", ","),  # type: ignore[arg-type]
            thousands_separator=raw.get("thousands_separator", "."),
            encoding=raw.get("encoding", encoding),
            delimiter=raw.get("delimiter", delimiter),
        )
    except (KeyError, ValueError, TypeError) as exc:
        log.warning("_llm_detect_format: ugyldigt LLM-svar: %s", exc)
        return None
