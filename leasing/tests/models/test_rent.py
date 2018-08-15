from datetime import date

import pytest

from leasing.enums import DueDatesType
from leasing.models import RentDueDate


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
        0,
        date(year=2017, month=6, day=30),
        None
    ),
    (
        1,
        date(year=2017, month=6, day=30),
        (date(year=2017, month=1, day=1), date(year=2017, month=12, day=31))
    ),
    (
        1,
        date(year=2017, month=1, day=1),
        None
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
    ),
    (
        4,
        date(year=2017, month=3, day=1),
        (date(year=2017, month=1, day=1), date(year=2017, month=3, day=31))
    ),
    (
        4,
        date(year=2017, month=4, day=15),
        (date(year=2017, month=4, day=1), date(year=2017, month=6, day=30))
    ),
    (
        4,
        date(year=2017, month=1, day=1),
        None
    ),
    (
        12,
        date(year=2017, month=1, day=1),
        (date(year=2017, month=1, day=1), date(year=2017, month=1, day=31))
    ),
    (
        12,
        date(year=2017, month=2, day=1),
        (date(year=2017, month=2, day=1), date(year=2017, month=2, day=28))
    ),
    (
        12,
        date(year=2017, month=6, day=1),
        (date(year=2017, month=6, day=1), date(year=2017, month=6, day=30))
    ),
    (
        12,
        date(year=2017, month=12, day=1),
        (date(year=2017, month=12, day=1), date(year=2017, month=12, day=31))
    ),
    (
        12,
        date(year=2017, month=1, day=10),
        None
    ),
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


@pytest.mark.django_db
@pytest.mark.parametrize("rent_due_dates, due_date, expected", [
    (
        [],
        None,
        None
    ),
    (
        [],
        date(year=2017, month=1, day=1),
        None
    ),
    (
        [(1, 1), (1, 10)],
        date(year=2017, month=5, day=1),
        None
    ),
    (
        [(1, 1), (1, 10)],
        date(year=2017, month=1, day=1),
        (date(year=2017, month=1, day=1), date(year=2017, month=6, day=30))
    ),
    (
        [(1, 1), (1, 10)],
        date(year=2017, month=10, day=1),
        (date(year=2017, month=7, day=1), date(year=2017, month=12, day=31))
    ),
])
def test_get_billing_period_from_due_date_custom(lease_test_data, rent_factory, rent_due_dates, due_date, expected):
    lease = lease_test_data['lease']

    rent = rent_factory(lease=lease)
    rent.start_date = date(year=2000, month=1, day=1)
    rent.end_date = date(year=2020, month=1, day=1)
    rent.due_dates_type = DueDatesType.CUSTOM
    rent.save()

    for rent_due_date in rent_due_dates:
        rent.due_dates.add(RentDueDate.objects.create(rent=rent, day=rent_due_date[0], month=rent_due_date[1]))

    assert rent.get_billing_period_from_due_date(due_date) == expected


@pytest.mark.django_db
@pytest.mark.parametrize("due_date, expected", [
    (
        None,
        None
    ),
    (
        date(year=2017, month=2, day=1),
        None
    ),
    (
        date(year=2017, month=1, day=1),
        (date(year=2017, month=1, day=1), date(year=2017, month=4, day=30))
    ),
])
def test_get_billing_period_from_due_date_seasonal(lease_test_data, rent_factory, due_date, expected):
    lease = lease_test_data['lease']

    rent = rent_factory(lease=lease)
    rent.start_date = date(year=2000, month=1, day=1)
    rent.end_date = date(year=2020, month=1, day=1)
    rent.seasonal_start_day = 1
    rent.seasonal_start_month = 1
    rent.seasonal_end_day = 30
    rent.seasonal_end_month = 4
    rent.due_dates_type = DueDatesType.CUSTOM
    rent.save()

    rent.due_dates.add(RentDueDate.objects.create(rent=rent, day=1, month=1))

    assert rent.get_billing_period_from_due_date(due_date) == expected


@pytest.mark.django_db
def test_get_billing_period_from_due_date_seasonal_fixed_due_date(lease_test_data, rent_factory):
    lease = lease_test_data['lease']

    rent = rent_factory(lease=lease)
    rent.start_date = date(year=2000, month=1, day=1)
    rent.end_date = date(year=2020, month=1, day=1)
    rent.seasonal_start_day = 1
    rent.seasonal_start_month = 1
    rent.seasonal_end_day = 30
    rent.seasonal_end_month = 4
    rent.due_dates_type = DueDatesType.FIXED
    rent.due_dates_per_year = 4
    rent.save()

    assert rent.get_billing_period_from_due_date(date(year=2017, month=5, day=1)) is None


@pytest.mark.django_db
@pytest.mark.parametrize("due_date, expected", [
    (
        None,
        None
    ),
    (
        date(year=2017, month=2, day=1),
        None
    ),
    (
        date(year=2017, month=7, day=1),
        (date(year=2017, month=6, day=1), date(year=2017, month=12, day=31))
    ),
])
def test_get_billing_period_from_due_date_seasonal_two_rents(lease_test_data, rent_factory, due_date, expected):
    lease = lease_test_data['lease']

    rent = rent_factory(lease=lease)
    rent.start_date = date(year=2000, month=1, day=1)
    rent.end_date = date(year=2020, month=1, day=1)
    rent.seasonal_start_day = 1
    rent.seasonal_start_month = 1
    rent.seasonal_end_day = 30
    rent.seasonal_end_month = 4
    rent.due_dates_type = DueDatesType.CUSTOM
    rent.save()

    rent.due_dates.add(RentDueDate.objects.create(rent=rent, day=1, month=1))

    rent2 = rent_factory(lease=lease)
    rent2.start_date = date(year=2000, month=1, day=1)
    rent2.end_date = date(year=2020, month=1, day=1)
    rent2.seasonal_start_day = 1
    rent2.seasonal_start_month = 6
    rent2.seasonal_end_day = 31
    rent2.seasonal_end_month = 12
    rent2.due_dates_type = DueDatesType.CUSTOM
    rent2.save()

    rent2.due_dates.add(RentDueDate.objects.create(rent=rent2, day=1, month=7))

    assert rent2.get_billing_period_from_due_date(due_date) == expected
