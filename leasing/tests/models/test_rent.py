from datetime import date

import pytest

from leasing.enums import DueDatesType


@pytest.mark.django_db
@pytest.mark.parametrize("due_dates_type, due_dates_per_year, start_date, end_date, expected", [
    # Too early
    (
        DueDatesType.FIXED,
        1,
        date(year=1990, month=1, day=1),
        date(year=1990, month=12, day=31),
        []
    ),
    # Too late
    (
        DueDatesType.FIXED,
        1,
        date(year=2030, month=1, day=1),
        date(year=2030, month=12, day=31),
        []
    ),
    # Full year
    (
        DueDatesType.FIXED,
        1,
        date(year=2017, month=1, day=1),
        date(year=2017, month=12, day=31),
        [date(year=2017, month=6, day=30)]
    ),
    (
        DueDatesType.FIXED,
        2,
        date(year=2017, month=1, day=1),
        date(year=2017, month=12, day=31),
        [date(year=2017, month=3, day=15), date(year=2017, month=9, day=30)]
    ),
    (
        DueDatesType.FIXED,
        3,
        date(year=2017, month=1, day=1),
        date(year=2017, month=12, day=31),
        []  # TODO
    ),
    (
        DueDatesType.FIXED,
        4,
        date(year=2017, month=1, day=1),
        date(year=2017, month=12, day=31),
        [date(year=2017, month=3, day=1), date(year=2017, month=4, day=15), date(year=2017, month=7, day=15),
            date(year=2017, month=10, day=15)]
    ),
    (
        DueDatesType.FIXED,
        12,
        date(year=2017, month=1, day=1),
        date(year=2017, month=12, day=31),
        [date(year=2017, month=i, day=1) for i in range(1, 13)]
    ),
])
def test_get_due_dates_for_period_fixed_middle(lease_test_data, rent_factory, due_dates_type, due_dates_per_year,
                                               start_date, end_date, expected):
    lease = lease_test_data['lease']

    rent = rent_factory(lease=lease)
    rent.start_date = date(year=2000, month=1, day=1)
    rent.end_date = date(year=2020, month=1, day=1)
    rent.due_dates_type = due_dates_type
    rent.due_dates_per_year = due_dates_per_year
    rent.save()

    assert rent.get_due_dates_for_period(start_date, end_date) == expected


@pytest.mark.django_db
@pytest.mark.parametrize("due_dates_per_year, due_date, expected", [
    (
        1,
        date(year=2017, month=6, day=30),
        (date(year=2017, month=1, day=1), date(year=2017, month=12, day=31))
    ),
    (
        2,
        date(year=2017, month=3, day=15),
        (date(year=2017, month=1, day=1), date(year=2017, month=6, day=30))
    ),
    (
        2,
        date(year=2017, month=9, day=30),
        (date(year=2017, month=7, day=1), date(year=2017, month=12, day=31))
    )
])
def test_get_billing_period_from_due_date(lease_test_data, rent_factory, due_dates_per_year, due_date,
                                          expected):
    lease = lease_test_data['lease']

    rent = rent_factory(lease=lease)
    rent.start_date = date(year=2000, month=1, day=1)
    rent.end_date = date(year=2020, month=1, day=1)
    rent.due_dates_type = DueDatesType.FIXED
    rent.due_dates_per_year = due_dates_per_year
    rent.save()

    assert rent.get_billing_period_from_due_date(due_date) == expected
