import os
from beancount import loader
from beanquery import query
from beancount.parser import printer


class BeancountConnector:
    def __init__(self, filename):
        if not os.path.exists(filename):
            raise FileNotFoundError(f"Regnskabsfilen '{filename}' blev ikke fundet.")

        self.filename = filename
        self.refresh()

    def refresh(self):
        """Genindlæser data fra filen (svarer til at opdatere en snapshot-view)."""
        self.entries, self.errors, self.options = loader.load_file(self.filename)
        if self.errors:
            print(f"Advarsel: Der blev fundet {len(self.errors)} fejl i regnskabet!")

    def execute(self, bql_query):
        """Eksekverer en BQL-forespørgsel (Beancount Query Language)."""
        column_names, row_tuples = query.run_query(
            self.entries, self.options, bql_query
        )
        return row_tuples

    def commit_entry(self, entry):
        """Skriver en ny transaktion/entry direkte til bunden af filen."""
        with open(self.filename, "a", encoding="utf-8") as f:
            f.write("\n")
            printer.print_entry(entry, file=f)
        self.refresh()  # Opdater hukommelsen efter skrivning

    def _in_period(self, qry, converter=None, start_date=None, end_date=None):
        res = [(d, amount) for d, amount in self.execute(qry)]
        if converter:
            res = [(d, converter(amount)) for d, amount in res]
        if start_date:
            res = [x for x in res if x[0] >= start_date]
        if end_date:
            res = [x for x in res if x[0] <= end_date]
        return res

    def account_in_period(self, account, start_date, end_date):
        return self._in_period(
            f"SELECT date, units(position) WHERE account ~ '{account}' ORDER BY date ASC",
            lambda x: x.number,
            start_date=start_date,
            end_date=end_date,
        )

    def account_sum_in_period(self, account, start_date, end_date):
        return sum(
            [a for d, a in self.account_in_period(account, start_date, end_date)]
        )

    def account_balance_in_period(self, account, start_date, end_date):
        return self._in_period(
            f"SELECT date, units(balance) WHERE account ~ '{account}' ORDER BY date ASC",
            lambda x: x.get_only_position().units.number,
            start_date=None,
            end_date=None,
        )

    def get_moms_status(self, start_date, end_date):
        return self.account_in_period("SkyldigMoms", None, start_date, end_date)
