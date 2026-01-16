from .transaction import Transaction
from .bank_transaction import BankTransaction
from datetime import date
from itertools import groupby
from . import util


def handle_afstem(ctx):
    print(f"Afstemning for {ctx.company_name} (enddate {ctx.enddate})")

    bc = ctx.get_connection()

    bank = "Assets:Bank:BankErhverv"

    t = bc.account_balance_in_period(bank, date(ctx.enddate.year, 1, 2), ctx.enddate)
    transactions = [(k, list(g)[-1][1]) for k, g in groupby(t, lambda x: x[0])]

    bank_csv = ctx.get_bank_csv(str(ctx.enddate.year))
    bank_transactions = dict(
        [
            (util.format_date(k), list(v)[-1])
            for k, v in groupby(
                BankTransaction.from_bank_csv(bank_csv), key=lambda x: x.date_posted
            )
        ]
    )

    afstemning = [
        (util.format_date(d), b, bank_transactions[util.format_date(d)].total)
        for d, b in transactions[1:]
        if util.format_date(d) in bank_transactions
    ]
    print("afstemningsdatoer:", len(afstemning))
    # print("\n".join([d[0] for d in afstemning]))

    first_diff = next((a for a in afstemning if a[1] != a[2]), None)
    if not first_diff:
        print("Bank stemmer med regnskab")
        return
    print(first_diff, first_diff[2] - first_diff[1])
