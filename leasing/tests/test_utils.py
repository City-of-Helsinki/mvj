from datetime import date
from math import isclose

from leasing.utils import calculate_increase_with_360_day_calendar, days360


def test_days360_year():
    date1 = date(year=2020, month=1, day=1)
    date2 = date(year=2021, month=1, day=1)

    days = days360(date1, date2, True)

    assert days == 360


def test_days360_leap_year():
    date1 = date(year=2020, month=1, day=15)
    date2 = date(year=2020, month=3, day=15)

    days = days360(date1, date2, True)

    assert days == 60


def test_calculate_increase_with_360_day_calendar():
    date1 = date(year=2020, month=8, day=3)
    date2 = date(year=2020, month=10, day=15)
    increase_percentage = 3
    current_amount = 150000.0
    expected_amount = 151000.0

    calculated_amount = calculate_increase_with_360_day_calendar(
        date1, date2, increase_percentage, current_amount
    )

    assert isclose(expected_amount, calculated_amount)
