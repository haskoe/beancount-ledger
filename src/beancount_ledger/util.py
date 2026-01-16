import pandas as pd
from datetime import datetime
from . import constants as const
from dateutil.relativedelta import relativedelta
from decimal import Decimal, ROUND_HALF_UP


def afrund_decimal(dec):
    return dec.quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def add_months(dt, months):
    return dt + relativedelta(months=months)


def first_day_of_month(dt):
    return dt.replace(day=1)


def last_day_of_month(dt):
    return first_day_of_month(add_months(dt, 1)) - relativedelta(days=1)


def format_money(num):
    return f"{num:.2f}"


def format_date(dt):
    return dt.strftime("%Y-%m-%d")


def date_parser(date_format):
    return lambda d: datetime.strptime(d, date_format)


def parse_date(dt):
    if dt is None:
        return None

    if isinstance(dt, datetime):
        return dt

    if not isinstance(dt, str):
        return None

    if isinstance(dt, str):
        try:
            return datetime.strptime(dt, "%Y%m%d").date()
        except ValueError:
            return datetime.strptime(dt, "%Y-%m-%d").date()


def get_bank_row_key(account_name, date_posted):
    return "%s_%s" % (account_name, date_posted.strftime("%Y%m%d"))


def combined_account(account_name, account_group):
    return "%s:%s" % (account_group, account_name)


try:
    decimal_separator = float("1%s1" % const.COMMA) == 1.1 and const.COMMA
except ValueError:
    decimal_separator = const.DOT
opposite_decimal_separator = (
    decimal_separator == const.COMMA and const.DOT or const.COMMA
)


def parse_amount(amount, decimal_separator_in_input):
    if decimal_separator_in_input == decimal_separator:
        return Decimal(amount.replace(opposite_decimal_separator, ""))

    return Decimal(
        amount.replace(decimal_separator, "").replace(
            decimal_separator_in_input, decimal_separator
        )
    )


# print(parse_amount("1.234,23", const.COMMA))
# print(parse_amount("1,234.23", const.DOT))

bank_date_parser = date_parser("%d-%m-%Y")


def load_csv(filename, spec, sep=const.SEMICOLON):
    dicts = pd.read_csv(
        filename,
        names=spec.keys(),
        sep=sep,
        encoding="utf-8",
        dtype=spec,
    ).to_dict(orient="records")
    return dicts


def csv_to_list(filename, spec, transformer=None):
    return [transformer and transformer(x) or x for x in load_csv(filename, spec)]


def csv_to_dict(filename, spec, transformer):
    tmp = load_csv(filename, spec)
    return dict([transformer(x) for x in tmp])


def write_file(filename, content, encoding="utf-8"):
    _write_file(filename, content, encoding=encoding)


def append_file(filename, content, encoding="utf-8"):
    _write_file(filename, content, encoding=encoding, mode="a")


def _write_file(filename, content, encoding="utf-8", mode="w"):
    with open(filename, mode, encoding=encoding) as f:
        if isinstance(content, list):
            f.write("\n".join(content))
        else:
            f.write(content)
