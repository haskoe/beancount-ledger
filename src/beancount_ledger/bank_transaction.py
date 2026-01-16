from dataclasses import dataclass
from . import util
from . import constants as const
from decimal import Decimal


@dataclass
class BankTransaction:
    date_posted: str
    description: str
    amount: Decimal
    total: Decimal

    def __post_init__(self):
        self.date_posted = util.bank_date_parser(self.date_posted)

    @staticmethod
    def from_bank_csv(rows):
        result = []
        for row in rows:
            result.append(
                BankTransaction(
                    date_posted=row[const.DATE_POSTED],
                    description=row[const.DESCRIPTION],
                    amount=util.parse_amount(row[const.AMOUNT], const.COMMA),
                    total=util.parse_amount(row[const.TOTAL], const.COMMA),
                )
            )

        return result
