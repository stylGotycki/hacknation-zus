"""Small date helpers (no third-party dependencies)."""

import calendar
from datetime import date, timedelta


def add_months(d: date, months: int) -> date:
    """Same day of the month `months` later; clamped to the last day (31 Jan + 1 = 28/29 Feb)."""
    index = d.year * 12 + (d.month - 1) + months
    year, month = divmod(index, 12)
    return date(year, month + 1, min(d.day, calendar.monthrange(year, month + 1)[1]))


def add_weeks(d: date, weeks: float) -> date:
    return d + timedelta(days=round(weeks * 7))


def end_of_period(start: date, days: int) -> date:
    """Last day of a period that starts on `start` and lasts `days` days (inclusive)."""
    return start + timedelta(days=max(days, 1) - 1)


def weeks_to_days(weeks: float) -> int:
    return round(weeks * 7)


def end_of_year(year: int) -> date:
    return date(year, 12, 31)


def full_years_between(earlier: date, later: date) -> int:
    years = later.year - earlier.year
    if (later.month, later.day) < (earlier.month, earlier.day):
        years -= 1
    return years
