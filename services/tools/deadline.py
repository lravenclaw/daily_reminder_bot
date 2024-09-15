from datetime import datetime, timedelta

def days_until_new_year():
    today = datetime.today()
    next_year = today.year + 1
    new_year_date = datetime(year=next_year, month=1, day=1)
    delta = new_year_date - today
    return delta.days