import calendar
from decimal import Decimal


def days360(start_date, end_date, method_eu=False):
    """
    Calculates the number of days for a period by using a 360-day calendar.
    """
    start_day = start_date.day
    start_month = start_date.month
    start_year = start_date.year
    end_day = end_date.day
    end_month = end_date.month
    end_year = end_date.year

    if start_day == 31 or (
        method_eu is False
        and start_month == 2
        and (
            start_day == 29
            or (start_day == 28 and calendar.isleap(start_year) is False)
        )
    ):
        start_day = 30

    if end_day == 31:
        if method_eu is False and start_day != 30:
            end_day = 1

            if end_month == 12:
                end_year += 1
                end_month = 1
            else:
                end_month += 1
        else:
            end_day = 30

    return (
        end_day
        + end_month * 30
        + end_year * 360
        - start_day
        - start_month * 30
        - start_year * 360
    )


def calculate_increase_with_360_day_calendar(
    date1, date2, increase_percentage, current_amount
):
    day_count = days360(date1, date2, True)
    increase_multiplier = Decimal(day_count) / 360 * Decimal(increase_percentage) / 100
    amount = Decimal(current_amount) + (
        Decimal(current_amount) * Decimal(increase_multiplier)
    )
    rounded_amount = round(amount, -3)
    return rounded_amount
