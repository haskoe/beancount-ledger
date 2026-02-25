import datetime

def parse_date(d: str, date_format: str) -> datetime.date:
    if isinstance(d, datetime.date):
        return d
    return datetime.datetime.strptime(str(d).strip(), date_format).date()

def add_days(dt: datetime.date, days: int) -> datetime.date:
    return (dt + datetime.timedelta(days=days))
