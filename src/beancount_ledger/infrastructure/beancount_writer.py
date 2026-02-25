"""Beancount fil-writer — append og overskriv-varianter (BR-01).

Bruges af alle application-services til at skrive posteringer
til .beancount-filer i generated/-mappen.
"""

from __future__ import annotations

from pathlib import Path

from beancount_ledger.domain.beancount_types import BeancountTransaction


def append_transaction(path: Path, txn: BeancountTransaction) -> None:
    """Tilføj én postering til en .beancount-fil.

    Opretter filen hvis den ikke eksisterer.
    Tilføjer ALTID til slutningen — eksisterende indhold ændres aldrig (BR-01).
    En tom linje indsættes som separator mellem posteringer.
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    text = txn.to_beancount() + "\n"

    if path.exists() and path.stat().st_size > 0:
        # Tilføj en tom separator-linje inden næste postering
        text = "\n" + text

    with path.open("a", encoding="utf-8") as fh:
        fh.write(text)


def append_transactions(path: Path, txns: list[BeancountTransaction]) -> None:
    """Tilføj flere posteringer til en .beancount-fil i én operation.

    Opretter filen hvis den ikke eksisterer.
    Posteringerne adskilles af en tom linje.
    Eksisterende indhold ændres aldrig (BR-01).
    """
    if not txns:
        return

    path.parent.mkdir(parents=True, exist_ok=True)

    blocks = [t.to_beancount() for t in txns]
    text = "\n\n".join(blocks) + "\n"

    if path.exists() and path.stat().st_size > 0:
        text = "\n" + text

    with path.open("a", encoding="utf-8") as fh:
        fh.write(text)


def write_transactions(
    path: Path,
    txns: list[BeancountTransaction],
    title: str = "",
) -> None:
    """Skriv (overskriv) en komplet .beancount-fil med *txns*.

    Bruges af services der regenererer hele filen ved hver kørsel,
    så manuelle rettelser i kildedata altid slår igennem.

    Filen oprettes i ``path.parent`` (opretter mapper hvis nødvendigt).
    En valgfri kommentarheader med *title* indsættes som første linje.
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = []
    if title:
        lines.append(f"; {title}\n")

    if txns:
        blocks = [t.to_beancount() for t in txns]
        lines.append("\n\n".join(blocks) + "\n")

    path.write_text("".join(lines), encoding="utf-8")


def ensure_beancount_header(path: Path, title: str = "") -> None:
    """Opret en .beancount-fil med valgfri kommentarheader, hvis den ikke allerede eksisterer.

    Gør ingenting hvis filen allerede eksisterer (BR-01).
    """
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    header = f"; {title}\n" if title else ""
    path.write_text(header, encoding="utf-8")
