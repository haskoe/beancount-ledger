from dataclasses import dataclass
from datetime import datetime, date
from functools import cached_property
from . import constants as const
from . import util
from decimal import Decimal


@dataclass
class Transaction:
    date_posted: date
    text: str
    extra_text: str
    amount: Decimal
    account1: str
    account2: str
    document: str
    template_name: str

    def __post_init__(self):
        if isinstance(self.date_posted, datetime):
            self.date_posted = self.date_posted.date()
        self.amount_abs = abs(self.amount)
        self.amount_vat_liable = 0
        self.amount_vat_non_liable = self.amount_abs
        self.vat_pct = 0
        self.account3 = ""

    def set_vat(self, account_vat, vat_pct, amount_vat_non_liable):
        self.account3 = account_vat
        self.amount_vat_non_liable = abs(amount_vat_non_liable)
        amount_vat_liable_including_vat = self.amount_abs - self.amount_vat_liable
        self.amount_vat_liable = amount_vat_liable_including_vat / (1 + vat_pct)
        self.vat_pct = vat_pct

    @cached_property
    def amount_wo_vat(self):
        return self.amount_vat_non_liable + self.amount_vat_liable

    @cached_property
    def vat(self):
        return self.amount_wo_vat * self.vat_pct

    @cached_property
    def all_accounts(self):
        return [
            a.strip()
            for a in (self.account1, self.account2, self.account3)
            if isinstance(a, str) and a.strip()
        ]

    @cached_property
    def as_dict(self):
        sign = 1 if self.amount > 0 else -1
        return {
            const.AMOUNT: util.format_money(self.amount),
            const.AMOUNT_NEGATED: util.format_money(-self.amount),
            const.ACCOUNT1: self.account1,
            const.ACCOUNT2: self.account2,
            const.ACCOUNT3: self.account3,
            const.AMOUNT_WO_VAT: util.format_money(sign * self.amount_wo_vat),
            const.VAT: util.format_money(sign * self.vat),
            const.AMOUNT_WO_VAT_NEGATED: util.format_money(-sign * self.amount_wo_vat),
            const.VAT_NEGATED: util.format_money(-sign * self.vat),
            const.CURRENCY: "DKK",  # todo
            const.TEXT: self.text,
            const.EXTRA_TEXT: self.extra_text,
            const.CURRENCY: "DKK",  # todo
            const.DATE_POSTED: util.format_date(self.date_posted),
            const.AMOUNT_WO_VAT_NEGATED: util.format_money(-sign * self.amount_wo_vat),
            const.VAT_NEGATED: util.format_money(-sign * self.vat),
            "document": self.document
            and f'external_link: "http://localhost:8000/{self.document}"'
            or None,
            # "date_posted": self.date_posted,
            # todo
            # "date_posted": self.date_posted,
            # "description": self.description,
            # "amount": self.amount,
            # "total": self.total,
            # "transaction_type": self.transaction_type,
            # "amount_vat_liable": self.amount_vat_liable,
            # "amount_vat_non_liable": self.amount_vat_non_liable,
            # "vat_pct": self.vat_pct,
        }

    @cached_property
    def is_vat(self):
        return "moms" in self.transaction_type[const.TEMPLATE_NAME]

    @staticmethod
    def from_salg_csv(rows, ctx):
        result = []
        for row in rows:
            account_name = row[const.ACCOUNT_NAME]
            yymmdd = datetime.strptime(row[const.YYMMDD], "%y%m%d")
            yymmdd_text = row[const.PERIOD_TXT]
            hours = Decimal(row[const.HOURS])
            support_hours = Decimal(row[const.SUPPORT_HOURS])

            hour_price = ctx.find_price(account_name, "Timepris", yymmdd)
            support_price = ctx.find_price(account_name, "Support", yymmdd)
            amount_wo_vat = hours * hour_price + support_hours * support_price
            price_text = f"Timer: {hours} * {hour_price} = {hours * hour_price}"
            if support_hours > 0:
                price_text += f". Support: {support_hours} * {support_price} = {support_hours * support_price}"

            transaction = Transaction(
                date_posted=yymmdd,
                text="Salg",
                extra_text=f"Salg {account_name}. Periode {yymmdd_text}. {price_text}",
                amount=amount_wo_vat * (1 + const.VAT_PCT),
                account1=f"Income:Salg:{account_name}",
                account2=f"Assets:Debitorer:{account_name}",
                document="20190702_121057_cd10fd68f0c094fd149ecc32e21088d9.jpg",
                template_name=const.MED_MOMS,
            )
            transaction.set_vat("Liabilities:Moms:SalgMoms", const.VAT_PCT, 0)
            result.append(transaction)
        return result

    @cached_property
    def company_path(self) -> str:
        return ""
