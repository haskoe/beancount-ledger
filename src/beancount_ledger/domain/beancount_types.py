"""Domænemodeller for beancount-posteringer.

Bruges af infrastructure/beancount_writer.py og application-laget
til at opbygge posteringer der skrives til .beancount-filer.
"""

from __future__ import annotations

import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, Field


class BeancountPosting(BaseModel):
    """Én debet/kredit-linje i en beancount-postering."""

    account: str = Field(..., min_length=1)
    amount: Decimal | None = None  # None → auto-balance
    currency: str = "DKK"
    comment: str = ""

    def to_beancount(self) -> str:
        """Returnér posteringslinjen som beancount-tekst."""
        if self.amount is not None:
            # Højrejuster beløbet i en fast bredde (beancount kræver det ikke, men det ser pænt ud)
            amount_str = f"{self.amount:.2f} {self.currency}"
            line = f"  {self.account:<52} {amount_str}"
        else:
            line = f"  {self.account}"
        if self.comment:
            line += f"  ; {self.comment}"
        return line

class BeancountTransaction(BaseModel):
    """En komplet beancount-postering med én eller flere kreditlinjer."""

    date: datetime.date
    flag: str = "*"
    payee: str | None = None
    narration: str
    links: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, str] = Field(default_factory=dict)
    postings: Annotated[list[BeancountPosting], Field(min_length=1)]

    def to_beancount(self) -> str:
        """Serialisér postering til beancount-format (én streng, ingen trailing newline)."""
        # Første linje: dato flag ["payee"] "narration" ^link #tag …
        if self.payee:
            header = f'{self.date} {self.flag} "{self.payee}" "{self.narration}"'
        else:
            header = f'{self.date} {self.flag} "{self.narration}"'
        for link in self.links:
            header += f" ^{link}"
        for tag in self.tags:
            header += f" #{tag}"

        lines: list[str] = [header]

        # Metadata-felter (key: "value")
        for key, value in self.metadata.items():
            lines.append(f'  {key}: "{value}"')

        # Kreditlinjer
        for posting in self.postings:
            lines.append(posting.to_beancount())

        return "\n".join(lines)
