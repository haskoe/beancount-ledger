import os
import re
from os import path
from collections import defaultdict
from datetime import datetime, date
from jinja2 import Environment, DictLoader
from dataclasses import dataclass
from .driver.connector import BeancountConnector
from . import constants as const
from . import util
from functools import cached_property
from decimal import Decimal


@dataclass
class LedgerContext:
    company_name: str
    enddate: date
    root_path: str = "."

    def __post_init__(self):
        if isinstance(self.enddate, str):
            try:
                self.enddate = datetime.strptime(self.enddate, "%Y%m%d").date()
            except ValueError:
                raise ValueError(f"Period {self.period} does not exist")

        if not self.enddate:
            self.enddate = datetime(int(self.period), 12, 31).date()

    @cached_property
    def periods(self) -> list[str]:
        period = int(self.enddate.strftime("%Y"))
        periods = sorted(
            [
                str(d)
                for d in os.listdir(self.company_path)
                if d.startswith("20") and int(d) <= period
            ]
        )
        print(periods)
        return periods

    @cached_property
    def company_path(self) -> str:
        print(self.company_name)
        return path.join(self.root_path, self.company_name)

    @cached_property
    def company_generated_path(self) -> str:
        return path.join(self.root_path, self.company_name, const.GENERATED_DIR)

    def company_period_path(self, period: str, filename: str) -> str:
        return path.join(self.company_path, period, filename)

    def company_metadata_path(self, filename: str) -> str:
        return path.join(self.company_path, "stamdata", filename)

    def write_file_in_generated_dir(self, filename: str, content) -> None:
        util.write_file(
            path.join(self.company_generated_path, filename),
            content,
        )

    def render_period_transactions(self, period: str, transactions) -> None:
        self.render_transactions(period, "", transactions)

    def render_transactions(self, period: str, prefix: str, transactions) -> None:
        output = []
        for t in transactions:
            if t.date_posted > self.enddate:
                continue
            template = self.get_template(t.template_name)
            output.append(template.render(t.as_dict))
        self.write_file_in_generated_dir(
            f"{prefix}{period}.beancount", "\n\n".join(output)
        )

    def write_period_file(self, period: str, content) -> None:
        self.write_file_in_generated_dir("%s.beancount" % (period,), content)

    def append_generated_file(self, period, prefix, content) -> None:
        util.append_file(
            path.join(self.company_generated_path, "%s.beancount" % (prefix,)),
            content,
        )

    def write_company_kontoplan_file(self, content) -> None:
        util.write_file(path.join(self.company_path, "kontoplan.beancount"), content)

    def get_connection(self) -> BeancountConnector:
        return BeancountConnector(path.join(self.company_path, "regnskab.beancount"))

    @cached_property
    def _jinja_env(self):
        return Environment(loader=DictLoader(templates_dict))

    def get_template(self, template_name: str):
        return self._jinja_env.get_template(template_name)

    @cached_property
    def all_accounts(self):
        return util.csv_to_dict(
            self.company_metadata_path(const.ACCOUNT_CSV),
            const.CSV_SPECS[const.ACCOUNT_CSV],
            lambda x: (
                x[const.ACCOUNT_NAME].casefold(),
                (
                    x[const.ACCOUNT_GROUP],
                    "%s:%s" % (x[const.ACCOUNT_GROUP], x[const.ACCOUNT_NAME]),
                ),
            ),
        )

    @cached_property
    def account_regexes(self):
        return util.csv_to_list(
            self.company_metadata_path(const.ACCOUNT_REGEX_CSV),
            const.CSV_SPECS[const.ACCOUNT_REGEX_CSV],
            lambda x: (
                x[const.ACCOUNT_NAME],
                re.compile(x[const.REGEX], re.IGNORECASE),
                x[const.REGEX].casefold(),
            ),
        )

    def get_bank_to_invoice_date(self, period: str):
        tmp = util.csv_to_dict(
            self.company_period_path(period, const.BANK_TO_INVOICE_DATE_CSV),
            const.CSV_SPECS[const.BANK_TO_INVOICE_DATE_CSV],
            lambda x: (";".join([x[const.DATE_POSTED_KEY], x[const.DESCRIPTION]]), x),
        )
        return tmp

    def get_bank_csv(self, period: str):
        return reversed(
            util.load_csv(
                self.company_period_path(period, "bank.csv"),
                const.CSV_SPECS[const.BANK_CSV],
            )
        )

    def get_loen_csv(self, period: str):
        return util.load_csv(
            self.company_period_path(period, "loen.txt"),
            const.CSV_SPECS[const.LOEN_CSV],
        )

    def get_udbytte_csv(self, period: str):
        return util.load_csv(
            self.company_period_path(period, "udbytte.txt"),
            const.CSV_SPECS[const.UDBYTTE_CSV],
        )

    @cached_property
    def prices(self):
        prices = defaultdict(lambda: defaultdict(list))
        for row in util.load_csv(
            self.company_metadata_path(const.PRICES_CSV),
            const.CSV_SPECS[const.PRICES_CSV],
        ):
            prices[row[const.ACCOUNT_NAME]][row[const.PRICE_TYPE]].append(
                (
                    datetime.strptime(row[const.YYMMDD], "%y%m%d"),
                    Decimal(row[const.PRICE]),
                )
            )
        # return {k: dict(v) for k, v in _prices.items()}
        return prices

    def get_salg_csv(self, period):
        return util.load_csv(
            self.company_period_path(period, "salg.txt"),
            const.CSV_SPECS[const.SALG_TXT],
        )

    @cached_property
    def transaction_types(self):
        return {
            "Liabilities": {
                const.ACCOUNT_GROUP: "Liabilities",
                const.ANTAL_POSTERINGER: 1,
                const.MED_MOMS: 0,
            },
            "Expenses": {
                const.ACCOUNT_GROUP: "Expenses",
                const.ANTAL_POSTERINGER: 1,
                const.MED_MOMS: 0,
            },
            "Expenses:Loen": {
                const.ACCOUNT_GROUP: "Expenses:Loen",
                const.ANTAL_POSTERINGER: 1,
                const.MED_MOMS: 0,
            },
            "Expenses:MedMoms": {
                const.ACCOUNT_GROUP: "Expenses:MedMoms",
                const.ANTAL_POSTERINGER: 2,
                const.MED_MOMS: 1,
            },
            "Expenses:UdenMoms": {
                const.ACCOUNT_GROUP: "Expenses:UdenMoms",
                const.ANTAL_POSTERINGER: 2,
                const.MED_MOMS: 0,
            },
            "Assets": {
                const.ACCOUNT_GROUP: "Assets",
                const.ANTAL_POSTERINGER: 1,
                const.MED_MOMS: 0,
            },
            "Income": {
                const.ACCOUNT_GROUP: "Income",
                const.ANTAL_POSTERINGER: 1,
                const.MED_MOMS: 0,
            },
        }

    def find_price(self, account_name, price_type, dt):
        matches_reversed = reversed(self.prices[account_name][price_type])
        return next((price for from_date, price in matches_reversed if from_date <= dt))


templates_dict = {
    "med_moms": """{{ date_posted }} * "{{ text }}" "{{ extra_text}}"
  {{ document }}
  {{ account1.ljust(50) }} {{ amount_wo_vat_negated.rjust(20) }} {{ currency }}
  {{ account2.ljust(50) }} {{ amount.rjust(20) }} {{ currency }}
  {{ account3.ljust(50) }} {{ vat_negated.rjust(20) }} {{ currency }}""",
    "uden_moms": """{{ date_posted }} * "{{ text }}" "{{ extra_text}}"
  {{ document }}
  {{ account1.ljust(50) }} {{ amount_negated.rjust(20) }} {{ currency }}
  {{ account2.ljust(50) }} {{ amount.rjust(20) }} {{ currency }}""",
    "moms_luk": """{{ date_posted }} * "Momsafregning" "Lukning af moms {{ period }}"
  {{ koebmoms_account.ljust(50) }} {{ koebmoms.rjust(20) }} {{ currency }}
  {{ salgmoms_account.ljust(50) }} {{ salgmoms.rjust(20) }} {{ currency }}
  {{ skyldigmoms_account.ljust(50) }} {{ skyldigmoms.rjust(20) }} {{ currency }}
  {{ afrunding_account.ljust(50) }} {{ afrunding.rjust(20) }} {{ currency }}""",
}
