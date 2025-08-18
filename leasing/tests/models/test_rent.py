import inspect
from datetime import date
from decimal import Decimal

import pytest

from leasing.enums import (
    DueDatesType,
    PeriodType,
    RentAdjustmentAmountType,
    RentAdjustmentType,
    RentCycle,
    RentType,
)
from leasing.models import Index, Rent, RentAdjustment, RentDueDate
from leasing.models.utils import DayMonth


@pytest.mark.django_db
@pytest.mark.parametrize(
    "rent_type, due_dates_per_year, expected",
    [
        (RentType.INDEX, 0, []),
        (RentType.INDEX, 3, []),
        (RentType.INDEX, 1, [DayMonth(day=30, month=6)]),
        (RentType.INDEX, 2, [DayMonth(day=15, month=3), DayMonth(day=30, month=9)]),
        (RentType.FIXED, 0, []),
        (RentType.FIXED, 3, []),
        (RentType.FIXED, 1, [DayMonth(day=2, month=1)]),
        (RentType.FIXED, 2, [DayMonth(day=2, month=1), DayMonth(day=1, month=7)]),
    ],
)
def test_fixed_get_due_dates_as_daymonths(
    lease_test_data, rent_factory, rent_type, due_dates_per_year, expected
):
    lease = lease_test_data["lease"]

    rent = rent_factory(lease=lease)
    rent.type = rent_type
    rent.start_date = date(year=2000, month=1, day=1)
    rent.end_date = date(year=2020, month=1, day=1)
    rent.due_dates_type = DueDatesType.FIXED
    rent.due_dates_per_year = due_dates_per_year
    rent.save()

    assert rent.get_due_dates_as_daymonths() == expected


@pytest.mark.django_db
@pytest.mark.parametrize(
    "due_dates_type, due_dates_per_year, start_date, end_date, expected",
    [
        (
            DueDatesType.FIXED,
            1,
            date(year=1990, month=1, day=1),
            date(year=1990, month=12, day=31),
            [date(year=1990, month=6, day=30)],
        ),
        (
            DueDatesType.FIXED,
            1,
            date(year=2030, month=1, day=1),
            date(year=2030, month=12, day=31),
            [date(year=2030, month=6, day=30)],
        ),
        # Full year
        (
            DueDatesType.FIXED,
            1,
            date(year=2017, month=1, day=1),
            date(year=2017, month=12, day=31),
            [date(year=2017, month=6, day=30)],
        ),
        (
            DueDatesType.FIXED,
            2,
            date(year=2017, month=1, day=1),
            date(year=2017, month=12, day=31),
            [date(year=2017, month=3, day=15), date(year=2017, month=9, day=30)],
        ),
        (
            DueDatesType.FIXED,
            3,
            date(year=2017, month=1, day=1),
            date(year=2017, month=12, day=31),
            [],  # TODO
        ),
        (
            DueDatesType.FIXED,
            4,
            date(year=2017, month=1, day=1),
            date(year=2017, month=12, day=31),
            [
                date(year=2017, month=3, day=1),
                date(year=2017, month=4, day=15),
                date(year=2017, month=7, day=15),
                date(year=2017, month=10, day=15),
            ],
        ),
        (
            DueDatesType.FIXED,
            12,
            date(year=2017, month=1, day=1),
            date(year=2017, month=12, day=31),
            [date(year=2017, month=i, day=1) for i in range(1, 13)],
        ),
    ],
)
def test_get_due_dates_for_period_fixed_middle(
    lease_test_data,
    rent_factory,
    due_dates_type,
    due_dates_per_year,
    start_date,
    end_date,
    expected,
):
    lease = lease_test_data["lease"]

    rent = rent_factory(lease=lease)
    rent.start_date = date(year=2000, month=1, day=1)
    rent.end_date = date(year=2020, month=1, day=1)
    rent.due_dates_type = due_dates_type
    rent.due_dates_per_year = due_dates_per_year
    rent.save()

    assert rent.get_due_dates_for_period(start_date, end_date) == expected


@pytest.mark.django_db
@pytest.mark.parametrize(
    "due_dates_per_year, due_date, expected",
    [
        (0, date(year=2017, month=6, day=30), None),
        (
            1,
            date(year=2017, month=6, day=30),
            (date(year=2017, month=1, day=1), date(year=2017, month=12, day=31)),
        ),
        (1, date(year=2017, month=1, day=1), None),
        (
            2,
            date(year=2017, month=3, day=15),
            (date(year=2017, month=1, day=1), date(year=2017, month=6, day=30)),
        ),
        (
            2,
            date(year=2017, month=9, day=30),
            (date(year=2017, month=7, day=1), date(year=2017, month=12, day=31)),
        ),
        (
            4,
            date(year=2017, month=3, day=1),
            (date(year=2017, month=1, day=1), date(year=2017, month=3, day=31)),
        ),
        (
            4,
            date(year=2017, month=4, day=15),
            (date(year=2017, month=4, day=1), date(year=2017, month=6, day=30)),
        ),
        (4, date(year=2017, month=1, day=1), None),
        (
            12,
            date(year=2017, month=1, day=1),
            (date(year=2017, month=1, day=1), date(year=2017, month=1, day=31)),
        ),
        (
            12,
            date(year=2017, month=2, day=1),
            (date(year=2017, month=2, day=1), date(year=2017, month=2, day=28)),
        ),
        (
            12,
            date(year=2017, month=6, day=1),
            (date(year=2017, month=6, day=1), date(year=2017, month=6, day=30)),
        ),
        (
            12,
            date(year=2017, month=12, day=1),
            (date(year=2017, month=12, day=1), date(year=2017, month=12, day=31)),
        ),
        (12, date(year=2017, month=1, day=10), None),
    ],
)
def test_get_billing_period_from_due_date(
    lease_test_data, rent_factory, due_dates_per_year, due_date, expected
):
    lease = lease_test_data["lease"]

    rent = rent_factory(lease=lease)
    rent.start_date = date(year=2000, month=1, day=1)
    rent.end_date = date(year=2020, month=1, day=1)
    rent.due_dates_type = DueDatesType.FIXED
    rent.due_dates_per_year = due_dates_per_year
    rent.save()

    assert rent.get_billing_period_from_due_date(due_date) == expected


@pytest.mark.django_db
@pytest.mark.parametrize(
    "rent_due_dates, due_date, expected",
    [
        ([], None, None),
        ([], date(year=2017, month=1, day=1), None),
        ([(1, 1), (1, 10)], date(year=2017, month=5, day=1), None),
        (
            [(1, 1), (1, 10)],
            date(year=2017, month=1, day=1),
            (date(year=2017, month=1, day=1), date(year=2017, month=6, day=30)),
        ),
        (
            [(1, 1), (1, 10)],
            date(year=2017, month=10, day=1),
            (date(year=2017, month=7, day=1), date(year=2017, month=12, day=31)),
        ),
    ],
)
def test_get_billing_period_from_due_date_custom(
    lease_test_data, rent_factory, rent_due_dates, due_date, expected
):
    lease = lease_test_data["lease"]

    rent = rent_factory(lease=lease)
    rent.start_date = date(year=2000, month=1, day=1)
    rent.end_date = date(year=2020, month=1, day=1)
    rent.due_dates_type = DueDatesType.CUSTOM
    rent.save()

    for rent_due_date in rent_due_dates:
        rent.due_dates.add(
            RentDueDate.objects.create(
                rent=rent, day=rent_due_date[0], month=rent_due_date[1]
            )
        )

    assert rent.get_billing_period_from_due_date(due_date) == expected


@pytest.mark.django_db
@pytest.mark.parametrize(
    "the_date, expected",
    [
        (None, 1927),  # the latest index in the fixtures
        (date(year=1000, month=1, day=1), None),
        (date(year=2016, month=12, day=1), 1906),
        (date(year=2017, month=1, day=1), 1913),
    ],
)
def test_index_get_latest_for_date(the_date, expected):
    index = Index.objects.get_latest_for_date(the_date)

    if expected is None:
        assert index is None
    else:
        assert index.month is None
        assert index.number == expected


@pytest.mark.django_db
@pytest.mark.parametrize(
    "year, expected",
    [
        (None, 1927),  # the latest index in the fixtures
        (1000, None),
        (2016, 1906),
        (2017, 1913),
        (2018, 1927),
    ],
)
def test_index_get_latest_for_year(year, expected):
    index = Index.objects.get_latest_for_year(year)

    if expected is None:
        assert index is None
    else:
        assert index.month is None
        assert index.number == expected


@pytest.mark.django_db
def test_get_amount_for_date_range_empty(lease_test_data, rent_factory):
    lease = lease_test_data["lease"]

    rent = rent_factory(
        lease=lease,
        cycle=RentCycle.JANUARY_TO_DECEMBER,
        due_dates_type=DueDatesType.FIXED,
        due_dates_per_year=1,
    )

    range_start = date(year=2018, month=1, day=1)
    range_end = date(year=2018, month=12, day=31)

    calculation_result = rent.get_amount_for_date_range(range_start, range_end)
    assert calculation_result.get_total_amount() == Decimal(0)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "amount, period, expected",
    [
        (Decimal(0), PeriodType.PER_YEAR, Decimal(0)),
        (Decimal(-100), PeriodType.PER_YEAR, Decimal(0)),
        (Decimal(10), PeriodType.PER_YEAR, Decimal("192.7")),
        (Decimal(100), PeriodType.PER_YEAR, Decimal(1927)),
        (Decimal(0), PeriodType.PER_MONTH, Decimal(0)),
        (Decimal(10), PeriodType.PER_MONTH, Decimal("2312.40")),
    ],
)
def test_get_amount_for_date_range_simple_contract(
    lease_test_data, rent_factory, contract_rent_factory, amount, period, expected
):
    lease = lease_test_data["lease"]

    rent = rent_factory(
        lease=lease,
        cycle=RentCycle.JANUARY_TO_DECEMBER,
        due_dates_type=DueDatesType.FIXED,
        due_dates_per_year=1,
    )

    contract_rent_factory(
        rent=rent,
        intended_use_id=1,
        amount=amount,
        period=period,
        base_amount=amount,
        base_amount_period=period,
    )

    range_start = date(year=2018, month=1, day=1)
    range_end = date(year=2018, month=12, day=31)

    calculation_result = rent.get_amount_for_date_range(range_start, range_end)
    assert calculation_result.get_total_amount() == expected


@pytest.mark.django_db
def test_get_amount_for_date_range_simple_contract_new_index(
    lease_test_data, rent_factory, contract_rent_factory
):
    lease = lease_test_data["lease"]

    rent = rent_factory(
        lease=lease,
        type=RentType.INDEX2022,
        cycle=RentCycle.JANUARY_TO_DECEMBER,
        due_dates_type=DueDatesType.FIXED,
        due_dates_per_year=1,
    )

    index = Index.objects.create(year=2020, month=6, number=1969)
    Index.objects.create(year=2021, month=None, number=2017)

    contract_rent_factory(
        rent=rent,
        intended_use_id=1,
        amount=Decimal(420000),
        period=PeriodType.PER_YEAR,
        base_amount=Decimal(420000),
        base_amount_period=PeriodType.PER_YEAR,
        index=index,
    )

    range_start = date(year=2022, month=1, day=1)
    range_end = date(year=2022, month=12, day=31)

    calculation_result = rent.get_amount_for_date_range(range_start, range_end)

    assert calculation_result.get_total_amount() == Decimal("430238.70")


@pytest.mark.django_db
def test_get_amount_for_date_range_with_adjustment_new_index(
    lease_test_data, rent_factory, contract_rent_factory, rent_adjustment_factory
):
    lease = lease_test_data["lease"]

    rent = rent_factory(
        lease=lease,
        type=RentType.INDEX2022,
        cycle=RentCycle.JANUARY_TO_DECEMBER,
        due_dates_type=DueDatesType.FIXED,
        due_dates_per_year=1,
    )

    index = Index.objects.create(year=2020, month=8, number=1977)
    Index.objects.create(year=2021, month=None, number=2017)

    contract_rent = contract_rent_factory(
        rent=rent,
        intended_use_id=1,
        amount=Decimal(249840),
        period=PeriodType.PER_YEAR,
        base_amount=Decimal(249840),
        base_amount_period=PeriodType.PER_YEAR,
        index=index,
    )

    rent_adjustment_factory(
        rent=rent,
        intended_use=contract_rent.intended_use,
        type=RentAdjustmentType.DISCOUNT,
        start_date=date(year=2020, month=1, day=1),
        end_date=date(year=2025, month=12, day=31),
        amount_type=RentAdjustmentAmountType.PERCENT_PER_YEAR,
        full_amount=20,
    )

    range_start = date(year=2022, month=1, day=1)
    range_end = date(year=2022, month=12, day=31)

    calculation_result = rent.get_amount_for_date_range(range_start, range_end)

    assert calculation_result.get_total_amount() == Decimal("203915.9440")


@pytest.mark.django_db
def test_get_amount_for_date_range_two_rents_new_index(
    lease_test_data, rent_factory, contract_rent_factory, rent_adjustment_factory
):
    lease = lease_test_data["lease"]

    rent = rent_factory(
        lease=lease,
        type=RentType.INDEX2022,
        cycle=RentCycle.JANUARY_TO_DECEMBER,
        due_dates_type=DueDatesType.FIXED,
        due_dates_per_year=1,
    )

    index = Index.objects.create(year=2019, month=3, number=1961)
    Index.objects.create(year=2021, month=None, number=2017)

    contract_rent_factory(
        rent=rent,
        intended_use_id=1,
        amount=Decimal(130000),
        period=PeriodType.PER_YEAR,
        base_amount=Decimal(130000),
        base_amount_period=PeriodType.PER_YEAR,
        index=index,
    )

    contract_rent_factory(
        rent=rent,
        intended_use_id=2,
        amount=Decimal(2720),
        period=PeriodType.PER_YEAR,
        base_amount=Decimal(2720),
        base_amount_period=PeriodType.PER_YEAR,
        index=index,
    )

    range_start = date(year=2022, month=1, day=1)
    range_end = date(year=2022, month=12, day=31)

    calculation_result = rent.get_amount_for_date_range(range_start, range_end)
    assert calculation_result.get_total_amount() == Decimal("136510.06")


@pytest.mark.django_db
@pytest.mark.parametrize(
    "range_start, range_end, expected",
    [
        (
            date(year=2017, month=1, day=1),
            date(year=2018, month=1, day=1),
            [
                (date(year=2017, month=1, day=1), date(year=2017, month=3, day=31)),
                (date(year=2017, month=4, day=1), date(year=2018, month=1, day=1)),
            ],
        ),
        (
            date(year=2017, month=1, day=1),
            date(year=2019, month=12, day=31),
            [
                (date(year=2017, month=1, day=1), date(year=2017, month=3, day=31)),
                (date(year=2017, month=4, day=1), date(year=2018, month=3, day=31)),
                (date(year=2018, month=4, day=1), date(year=2019, month=3, day=31)),
                (date(year=2019, month=4, day=1), date(year=2019, month=12, day=31)),
            ],
        ),
        (
            date(year=2018, month=1, day=1),
            date(year=2018, month=1, day=31),
            [(date(year=2018, month=1, day=1), date(year=2018, month=1, day=31))],
        ),
        (
            date(year=2018, month=1, day=1),
            date(year=2018, month=3, day=31),
            [(date(year=2018, month=1, day=1), date(year=2018, month=3, day=31))],
        ),
        (
            date(year=2018, month=4, day=1),
            date(year=2018, month=12, day=31),
            [(date(year=2018, month=4, day=1), date(year=2018, month=12, day=31))],
        ),
        (
            date(year=2018, month=3, day=31),
            date(year=2018, month=4, day=1),
            [(date(year=2018, month=3, day=31), date(year=2018, month=4, day=1))],
        ),
        (
            date(year=2018, month=1, day=1),
            date(year=2018, month=12, day=31),
            [
                (date(year=2018, month=1, day=1), date(year=2018, month=3, day=31)),
                (date(year=2018, month=4, day=1), date(year=2018, month=12, day=31)),
            ],
        ),
        (
            date(year=2018, month=3, day=1),
            date(year=2018, month=6, day=15),
            [
                (date(year=2018, month=3, day=1), date(year=2018, month=3, day=31)),
                (date(year=2018, month=4, day=1), date(year=2018, month=6, day=15)),
            ],
        ),
    ],
)
def test_split_range_by_cycle(
    lease_test_data, rent_factory, range_start, range_end, expected
):
    lease = lease_test_data["lease"]

    rent = rent_factory(
        lease=lease,
        cycle=RentCycle.APRIL_TO_MARCH,
        due_dates_type=DueDatesType.FIXED,
        due_dates_per_year=1,
    )

    if inspect.isclass(expected) and issubclass(expected, Exception):
        with pytest.raises(expected):
            rent.split_range_by_cycle(range_start, range_end)
    else:
        assert rent.split_range_by_cycle(range_start, range_end) == expected


@pytest.mark.django_db
@pytest.mark.parametrize(
    "cycle, range_start, range_end, expected",
    [
        (
            RentCycle.JANUARY_TO_DECEMBER,
            date(year=2017, month=1, day=1),
            date(year=2017, month=12, day=31),
            [(date(year=2017, month=1, day=1), date(year=2017, month=12, day=31))],
        ),
        (
            RentCycle.JANUARY_TO_DECEMBER,
            date(year=2017, month=5, day=1),
            date(year=2017, month=8, day=31),
            [(date(year=2017, month=5, day=1), date(year=2017, month=8, day=31))],
        ),
        (
            RentCycle.JANUARY_TO_DECEMBER,
            date(year=2017, month=6, day=1),
            date(year=2018, month=5, day=31),
            [
                (date(year=2017, month=6, day=1), date(year=2017, month=12, day=31)),
                (date(year=2018, month=1, day=1), date(year=2018, month=5, day=31)),
            ],
        ),
        (
            RentCycle.APRIL_TO_MARCH,
            date(year=2017, month=4, day=1),
            date(year=2018, month=3, day=31),
            [(date(year=2017, month=4, day=1), date(year=2018, month=3, day=31))],
        ),
        (
            RentCycle.APRIL_TO_MARCH,
            date(year=2017, month=1, day=1),
            date(year=2018, month=12, day=31),
            [
                (date(year=2017, month=1, day=1), date(year=2017, month=3, day=31)),
                (date(year=2017, month=4, day=1), date(year=2018, month=3, day=31)),
                (date(year=2018, month=4, day=1), date(year=2018, month=12, day=31)),
            ],
        ),
    ],
)
def test_split_range_by_cycle_span_year_boundary(
    lease_test_data, rent_factory, cycle, range_start, range_end, expected
):
    lease = lease_test_data["lease"]

    rent = rent_factory(
        lease=lease,
        cycle=cycle,
        due_dates_type=DueDatesType.FIXED,
        due_dates_per_year=1,
    )

    if inspect.isclass(expected) and issubclass(expected, Exception):
        with pytest.raises(expected):
            rent.split_range_by_cycle(range_start, range_end)
    else:
        assert rent.split_range_by_cycle(range_start, range_end) == expected


@pytest.mark.django_db
@pytest.mark.parametrize(
    "ranges, expected",
    [
        (
            [(date(year=2018, month=1, day=1), date(year=2018, month=1, day=31))],
            [(date(year=2018, month=1, day=1), date(year=2018, month=1, day=31))],
        ),
        (
            [
                (date(year=2018, month=1, day=1), date(year=2018, month=1, day=31)),
                (date(year=2018, month=1, day=1), date(year=2018, month=1, day=31)),
            ],
            [
                (date(year=2018, month=1, day=1), date(year=2018, month=1, day=31)),
                (date(year=2018, month=1, day=1), date(year=2018, month=1, day=31)),
            ],
        ),
        (
            [
                (date(year=2018, month=1, day=1), date(year=2018, month=1, day=31)),
                (date(year=2018, month=1, day=1), date(year=2018, month=12, day=31)),
            ],
            [
                (date(year=2018, month=1, day=1), date(year=2018, month=1, day=31)),
                (date(year=2018, month=1, day=1), date(year=2018, month=3, day=31)),
                (date(year=2018, month=4, day=1), date(year=2018, month=12, day=31)),
            ],
        ),
        (
            [
                (date(year=2018, month=1, day=1), date(year=2018, month=6, day=30)),
                (date(year=2018, month=3, day=1), date(year=2018, month=10, day=31)),
            ],
            [
                (date(year=2018, month=1, day=1), date(year=2018, month=3, day=31)),
                (date(year=2018, month=4, day=1), date(year=2018, month=6, day=30)),
                (date(year=2018, month=3, day=1), date(year=2018, month=3, day=31)),
                (date(year=2018, month=4, day=1), date(year=2018, month=10, day=31)),
            ],
        ),
    ],
)
def test_split_ranges_by_cycle(lease_test_data, rent_factory, ranges, expected):
    lease = lease_test_data["lease"]

    rent = rent_factory(
        lease=lease,
        cycle=RentCycle.APRIL_TO_MARCH,
        due_dates_type=DueDatesType.FIXED,
        due_dates_per_year=1,
    )

    if inspect.isclass(expected) and issubclass(expected, Exception):
        with pytest.raises(expected):
            rent.split_ranges_by_cycle(ranges)
    else:
        assert rent.split_ranges_by_cycle(ranges) == expected


@pytest.mark.django_db
@pytest.mark.parametrize(
    "rent_cycle, the_date, expected",
    [
        (RentCycle.JANUARY_TO_DECEMBER, date(year=2016, month=1, day=1), 2016),
        (RentCycle.JANUARY_TO_DECEMBER, date(year=2017, month=1, day=1), 2017),
        (RentCycle.JANUARY_TO_DECEMBER, date(year=2018, month=1, day=1), 2018),
        (RentCycle.JANUARY_TO_DECEMBER, date(year=2018, month=6, day=1), 2018),
        (RentCycle.JANUARY_TO_DECEMBER, date(year=2018, month=12, day=31), 2018),
        (RentCycle.JANUARY_TO_DECEMBER, date(year=2019, month=1, day=1), 2019),
        (RentCycle.JANUARY_TO_DECEMBER, date(year=2020, month=1, day=1), 2020),
        (RentCycle.APRIL_TO_MARCH, date(year=2016, month=1, day=1), 2015),
        (RentCycle.APRIL_TO_MARCH, date(year=2017, month=1, day=1), 2016),
        (RentCycle.APRIL_TO_MARCH, date(year=2018, month=1, day=1), 2017),
        (RentCycle.APRIL_TO_MARCH, date(year=2018, month=6, day=1), 2018),
        (RentCycle.APRIL_TO_MARCH, date(year=2018, month=12, day=31), 2018),
        (RentCycle.APRIL_TO_MARCH, date(year=2019, month=1, day=1), 2018),
        (RentCycle.APRIL_TO_MARCH, date(year=2020, month=1, day=1), 2019),
        (RentCycle.APRIL_TO_MARCH, date(year=2020, month=4, day=1), 2020),
    ],
)
def test_get_rent_year_for_date(
    lease_test_data, rent_factory, rent_cycle, the_date, expected
):
    lease = lease_test_data["lease"]

    rent = rent_factory(
        lease=lease,
        start_date=date(year=2000, month=1, day=1),
        end_date=date(year=2020, month=1, day=1),
        due_dates_type=DueDatesType.FIXED,
        due_dates_per_year=1,
        cycle=rent_cycle,
    )

    assert rent.get_rent_year_for_date(the_date) == expected


@pytest.mark.django_db
@pytest.mark.parametrize(
    "rent_cycle, the_date, expected",
    [
        # Index numbers are from the fixtures. 2017 index number (1927) is the latest.
        (RentCycle.JANUARY_TO_DECEMBER, date(year=2016, month=1, day=1), 1906),
        (RentCycle.JANUARY_TO_DECEMBER, date(year=2017, month=1, day=1), 1913),
        (RentCycle.JANUARY_TO_DECEMBER, date(year=2018, month=1, day=1), 1927),
        (RentCycle.JANUARY_TO_DECEMBER, date(year=2018, month=6, day=1), 1927),
        (RentCycle.JANUARY_TO_DECEMBER, date(year=2018, month=12, day=31), 1927),
        (RentCycle.JANUARY_TO_DECEMBER, date(year=2019, month=1, day=1), 1927),
        (RentCycle.JANUARY_TO_DECEMBER, date(year=2020, month=1, day=1), 1927),
        (RentCycle.APRIL_TO_MARCH, date(year=2016, month=1, day=1), 1910),
        (RentCycle.APRIL_TO_MARCH, date(year=2017, month=1, day=1), 1906),
        (RentCycle.APRIL_TO_MARCH, date(year=2018, month=1, day=1), 1913),
        (RentCycle.APRIL_TO_MARCH, date(year=2018, month=6, day=1), 1927),
        (RentCycle.APRIL_TO_MARCH, date(year=2018, month=12, day=31), 1927),
        (RentCycle.APRIL_TO_MARCH, date(year=2019, month=1, day=1), 1927),
        (RentCycle.APRIL_TO_MARCH, date(year=2020, month=1, day=1), 1927),
    ],
)
def test_get_index_for_date(
    lease_test_data, rent_factory, rent_cycle, the_date, expected
):
    lease = lease_test_data["lease"]

    rent = rent_factory(
        lease=lease,
        start_date=date(year=2000, month=1, day=1),
        end_date=date(year=2020, month=1, day=1),
        due_dates_type=DueDatesType.FIXED,
        due_dates_per_year=1,
        cycle=rent_cycle,
    )

    assert rent.get_index_for_date(the_date).number == expected


@pytest.mark.django_db
@pytest.mark.parametrize(
    "rent_cycle, the_date, index_year_month, expected",
    [
        (
            RentCycle.JANUARY_TO_DECEMBER,
            date(year=2017, month=1, day=1),
            (2015, None),
            False,
        ),
        (
            RentCycle.JANUARY_TO_DECEMBER,
            date(year=2017, month=1, day=1),
            (2016, None),
            True,
        ),
        (
            RentCycle.JANUARY_TO_DECEMBER,
            date(year=2017, month=1, day=1),
            (2016, 1),
            False,
        ),
        (
            RentCycle.JANUARY_TO_DECEMBER,
            date(year=2017, month=1, day=1),
            (2016, 12),
            False,
        ),
        (
            RentCycle.JANUARY_TO_DECEMBER,
            date(year=2017, month=6, day=1),
            (2016, None),
            True,
        ),
        (
            RentCycle.JANUARY_TO_DECEMBER,
            date(year=2017, month=12, day=31),
            (2016, None),
            True,
        ),
        (
            RentCycle.JANUARY_TO_DECEMBER,
            date(year=2019, month=1, day=1),
            (2018, None),
            True,
        ),
        (
            RentCycle.JANUARY_TO_DECEMBER,
            date(year=2020, month=1, day=1),
            (2019, None),
            True,
        ),
        (RentCycle.APRIL_TO_MARCH, date(year=2017, month=1, day=1), (2015, None), True),
        (
            RentCycle.APRIL_TO_MARCH,
            date(year=2017, month=1, day=1),
            (2016, None),
            False,
        ),
        (RentCycle.APRIL_TO_MARCH, date(year=2017, month=1, day=1), (2016, 1), False),
        (RentCycle.APRIL_TO_MARCH, date(year=2017, month=1, day=1), (2016, 12), False),
        (RentCycle.APRIL_TO_MARCH, date(year=2017, month=6, day=1), (2016, None), True),
        (
            RentCycle.APRIL_TO_MARCH,
            date(year=2017, month=12, day=31),
            (2016, None),
            True,
        ),
        (
            RentCycle.APRIL_TO_MARCH,
            date(year=2019, month=1, day=1),
            (2018, None),
            False,
        ),
        (
            RentCycle.APRIL_TO_MARCH,
            date(year=2020, month=1, day=1),
            (2019, None),
            False,
        ),
        (RentCycle.APRIL_TO_MARCH, date(year=2019, month=4, day=1), (2018, None), True),
        (RentCycle.APRIL_TO_MARCH, date(year=2020, month=4, day=1), (2019, None), True),
    ],
)
def test_is_correct_index_for_date(
    lease_test_data, rent_factory, rent_cycle, the_date, index_year_month, expected
):
    lease = lease_test_data["lease"]

    index = Index(year=index_year_month[0], month=index_year_month[1], number=12345)

    rent = rent_factory(
        lease=lease,
        start_date=date(year=2000, month=1, day=1),
        end_date=date(year=2020, month=1, day=1),
        due_dates_type=DueDatesType.FIXED,
        due_dates_per_year=1,
        cycle=rent_cycle,
    )

    assert rent.is_correct_index_for_date(index, the_date) == expected


@pytest.mark.django_db
@pytest.mark.parametrize(
    "amount, period, expected",
    [
        (Decimal(0), PeriodType.PER_YEAR, Decimal(0)),
        (Decimal(-100), PeriodType.PER_YEAR, Decimal(0)),
        (Decimal(10), PeriodType.PER_YEAR, Decimal("192.35")),
        (Decimal(100), PeriodType.PER_YEAR, Decimal("1923.5")),
        (Decimal(0), PeriodType.PER_MONTH, Decimal(0)),
    ],
)
def test_get_amount_for_date_range_simple_contract_april_to_march(
    lease_test_data, rent_factory, contract_rent_factory, amount, period, expected
):
    lease = lease_test_data["lease"]

    rent = rent_factory(
        lease=lease,
        cycle=RentCycle.APRIL_TO_MARCH,
        due_dates_type=DueDatesType.FIXED,
        due_dates_per_year=1,
    )

    contract_rent_factory(
        rent=rent,
        intended_use_id=1,
        amount=amount,
        period=period,
        base_amount=amount,
        base_amount_period=period,
    )

    range_start = date(year=2018, month=1, day=1)
    range_end = date(year=2018, month=12, day=31)

    calculation_result = rent.get_amount_for_date_range(range_start, range_end)
    assert calculation_result.get_total_amount() == expected


@pytest.mark.django_db
@pytest.mark.parametrize(
    "adjustment_type, adjustment_start_date, adjustment_end_date, adjustment_amount_type, adjustment_amount, expected",
    [
        # Discount
        # Amount per year
        (
            RentAdjustmentType.DISCOUNT,
            None,
            None,
            RentAdjustmentAmountType.AMOUNT_PER_YEAR,
            27,
            Decimal(73),
        ),
        (
            RentAdjustmentType.DISCOUNT,
            date(year=2017, month=1, day=1),
            date(year=2019, month=12, day=31),
            RentAdjustmentAmountType.AMOUNT_PER_YEAR,
            0,
            Decimal(100),
        ),
        (
            RentAdjustmentType.DISCOUNT,
            date(year=2017, month=1, day=1),
            date(year=2019, month=12, day=31),
            RentAdjustmentAmountType.AMOUNT_PER_YEAR,
            100,
            Decimal(0),
        ),
        (
            RentAdjustmentType.DISCOUNT,
            date(year=2017, month=1, day=1),
            date(year=2019, month=12, day=31),
            RentAdjustmentAmountType.AMOUNT_PER_YEAR,
            2000,
            Decimal(0),
        ),
        (
            RentAdjustmentType.DISCOUNT,
            date(year=2017, month=1, day=1),
            date(year=2019, month=12, day=31),
            RentAdjustmentAmountType.AMOUNT_PER_YEAR,
            -100,
            Decimal(200),
        ),
        # Percent per year
        (
            RentAdjustmentType.DISCOUNT,
            date(year=2017, month=1, day=1),
            date(year=2019, month=12, day=31),
            RentAdjustmentAmountType.PERCENT_PER_YEAR,
            0,
            Decimal(100),
        ),
        (
            RentAdjustmentType.DISCOUNT,
            date(year=2017, month=1, day=1),
            date(year=2019, month=12, day=31),
            RentAdjustmentAmountType.PERCENT_PER_YEAR,
            -100,
            Decimal(200),
        ),
        (
            RentAdjustmentType.DISCOUNT,
            date(year=2017, month=1, day=1),
            date(year=2019, month=12, day=31),
            RentAdjustmentAmountType.PERCENT_PER_YEAR,
            100,
            Decimal(0),
        ),
        (
            RentAdjustmentType.DISCOUNT,
            date(year=2017, month=1, day=1),
            date(year=2019, month=12, day=31),
            RentAdjustmentAmountType.PERCENT_PER_YEAR,
            120,
            Decimal(0),
        ),
        (
            RentAdjustmentType.DISCOUNT,
            date(year=2017, month=1, day=1),
            date(year=2019, month=12, day=31),
            RentAdjustmentAmountType.PERCENT_PER_YEAR,
            50,
            Decimal(50),
        ),
        (
            RentAdjustmentType.DISCOUNT,
            date(year=2018, month=1, day=1),
            date(year=2018, month=12, day=31),
            RentAdjustmentAmountType.PERCENT_PER_YEAR,
            50,
            Decimal(50),
        ),
        (
            RentAdjustmentType.DISCOUNT,
            date(year=2018, month=7, day=1),
            date(year=2018, month=12, day=31),
            RentAdjustmentAmountType.PERCENT_PER_YEAR,
            50,
            Decimal(75),
        ),
        (
            RentAdjustmentType.DISCOUNT,
            date(year=2018, month=1, day=1),
            date(year=2018, month=6, day=30),
            RentAdjustmentAmountType.PERCENT_PER_YEAR,
            50,
            Decimal(75),
        ),
        # Increase
        # Amount per year
        (
            RentAdjustmentType.INCREASE,
            None,
            None,
            RentAdjustmentAmountType.AMOUNT_PER_YEAR,
            100,
            Decimal(200),
        ),
        (
            RentAdjustmentType.INCREASE,
            date(year=2017, month=1, day=1),
            date(year=2019, month=12, day=31),
            RentAdjustmentAmountType.AMOUNT_PER_YEAR,
            0,
            Decimal(100),
        ),
        (
            RentAdjustmentType.INCREASE,
            date(year=2017, month=1, day=1),
            date(year=2019, month=12, day=31),
            RentAdjustmentAmountType.AMOUNT_PER_YEAR,
            -10,
            Decimal(90),
        ),
        (
            RentAdjustmentType.INCREASE,
            date(year=2017, month=1, day=1),
            date(year=2019, month=12, day=31),
            RentAdjustmentAmountType.AMOUNT_PER_YEAR,
            -200,
            Decimal(0),
        ),
        (
            RentAdjustmentType.INCREASE,
            date(year=2017, month=1, day=1),
            date(year=2019, month=12, day=31),
            RentAdjustmentAmountType.AMOUNT_PER_YEAR,
            200,
            Decimal(300),
        ),
        # Percent per year
        (
            RentAdjustmentType.INCREASE,
            date(year=2017, month=1, day=1),
            date(year=2019, month=12, day=31),
            RentAdjustmentAmountType.PERCENT_PER_YEAR,
            0,
            Decimal(100),
        ),
        (
            RentAdjustmentType.INCREASE,
            date(year=2017, month=1, day=1),
            date(year=2019, month=12, day=31),
            RentAdjustmentAmountType.PERCENT_PER_YEAR,
            50,
            Decimal(150),
        ),
        (
            RentAdjustmentType.INCREASE,
            date(year=2018, month=1, day=1),
            date(year=2018, month=12, day=31),
            RentAdjustmentAmountType.PERCENT_PER_YEAR,
            50,
            Decimal(150),
        ),
        (
            RentAdjustmentType.INCREASE,
            date(year=2018, month=7, day=1),
            date(year=2018, month=12, day=31),
            RentAdjustmentAmountType.PERCENT_PER_YEAR,
            50,
            Decimal(125),
        ),
        (
            RentAdjustmentType.INCREASE,
            date(year=2018, month=1, day=1),
            date(year=2018, month=6, day=30),
            RentAdjustmentAmountType.PERCENT_PER_YEAR,
            50,
            Decimal(125),
        ),
    ],
)
def test_get_amount_for_date_range_contract_with_adjustment(
    lease_test_data,
    rent_factory,
    contract_rent_factory,
    rent_adjustment_factory,
    adjustment_type,
    adjustment_start_date,
    adjustment_end_date,
    adjustment_amount_type,
    adjustment_amount,
    expected,
):
    lease = lease_test_data["lease"]

    rent = rent_factory(
        lease=lease,
        type=RentType.FIXED,
        cycle=RentCycle.JANUARY_TO_DECEMBER,
        due_dates_type=DueDatesType.FIXED,
        due_dates_per_year=1,
    )

    contract_rent = contract_rent_factory(
        rent=rent,
        intended_use_id=1,
        amount=Decimal(100),
        period=PeriodType.PER_YEAR,
        base_amount=Decimal(100),
        base_amount_period=PeriodType.PER_YEAR,
    )

    rent_adjustment_factory(
        rent=rent,
        intended_use=contract_rent.intended_use,
        type=adjustment_type,
        start_date=adjustment_start_date,
        end_date=adjustment_end_date,
        amount_type=adjustment_amount_type,
        full_amount=adjustment_amount,
    )

    range_start = date(year=2018, month=1, day=1)
    range_end = date(year=2018, month=12, day=31)

    calculation_result = rent.get_amount_for_date_range(range_start, range_end)
    assert calculation_result.get_total_amount() == expected


@pytest.mark.django_db
def test_get_amount_for_date_range_contract_with_adjustment_different_intended_use(
    lease_test_data, rent_factory, contract_rent_factory, rent_adjustment_factory
):
    lease = lease_test_data["lease"]

    rent = rent_factory(
        lease=lease,
        cycle=RentCycle.JANUARY_TO_DECEMBER,
        due_dates_type=DueDatesType.FIXED,
        due_dates_per_year=1,
    )

    contract_rent_factory(
        rent=rent,
        intended_use_id=1,
        amount=Decimal(100),
        period=PeriodType.PER_YEAR,
        base_amount=Decimal(100),
        base_amount_period=PeriodType.PER_YEAR,
    )

    rent_adjustment_factory(
        rent=rent,
        intended_use_id=2,
        type=RentAdjustmentType.DISCOUNT,
        start_date=None,
        end_date=None,
        amount_type=RentAdjustmentAmountType.PERCENT_PER_YEAR,
        full_amount=50,
    )

    range_start = date(year=2018, month=1, day=1)
    range_end = date(year=2018, month=12, day=31)

    calculation_result = rent.get_amount_for_date_range(range_start, range_end)
    assert calculation_result.get_total_amount() == Decimal(1927)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "fixed_initial_amount, fixed_initial_start_date, fixed_initial_end_date, expected",
    [
        (
            0,
            date(year=2017, month=1, day=1),
            date(year=2019, month=12, day=31),
            Decimal(0),
        ),
        (
            -100,
            date(year=2017, month=1, day=1),
            date(year=2019, month=12, day=31),
            # TODO: Is negative fixed initial year rent allowed?
            # Decimal(-100)
            Decimal(0),
        ),
        (
            100,
            date(year=2017, month=1, day=1),
            date(year=2019, month=12, day=31),
            Decimal(100),
        ),
        (
            100,
            date(year=2017, month=1, day=1),
            date(year=2018, month=6, day=30),
            Decimal("1013.5"),
        ),
        (
            100,
            date(year=2017, month=1, day=1),
            date(year=2017, month=1, day=1),
            Decimal(1927),
        ),
        (
            100,
            date(year=2019, month=1, day=1),
            date(year=2019, month=1, day=1),
            Decimal(1927),
        ),
        (
            1200,
            date(year=2018, month=3, day=1),
            date(year=2018, month=3, day=31),
            pytest.approx(Decimal("1866.416")),
        ),
    ],
)
def test_get_amount_for_date_range_contract_with_fixed_initial(
    lease_test_data,
    rent_factory,
    contract_rent_factory,
    fixed_initial_year_rent_factory,
    fixed_initial_amount,
    fixed_initial_start_date,
    fixed_initial_end_date,
    expected,
):

    lease = lease_test_data["lease"]

    rent = rent_factory(
        lease=lease,
        cycle=RentCycle.JANUARY_TO_DECEMBER,
        due_dates_type=DueDatesType.FIXED,
        due_dates_per_year=1,
    )

    contract_rent = contract_rent_factory(
        rent=rent,
        intended_use_id=1,
        amount=Decimal(100),
        period=PeriodType.PER_YEAR,
        base_amount=Decimal(100),
        base_amount_period=PeriodType.PER_YEAR,
    )

    fixed_initial_year_rent_factory(
        rent=rent,
        intended_use=contract_rent.intended_use,
        amount=fixed_initial_amount,
        start_date=fixed_initial_start_date,
        end_date=fixed_initial_end_date,
    )

    range_start = date(year=2018, month=1, day=1)
    range_end = date(year=2018, month=12, day=31)

    calculation_result = rent.get_amount_for_date_range(range_start, range_end)
    assert calculation_result.get_total_amount() == expected


@pytest.mark.django_db
@pytest.mark.parametrize(
    "adjustment_type, adjustment_start_date, adjustment_end_date, adjustment_amount_type, adjustment_amount, "
    "fixed_initial_amount, fixed_initial_start_date, fixed_initial_end_date, expected",
    [
        (
            # Rent adjustment
            RentAdjustmentType.DISCOUNT,
            date(year=2018, month=1, day=1),
            date(year=2018, month=12, day=31),
            RentAdjustmentAmountType.PERCENT_PER_YEAR,
            0,
            # Fixed initial year rent
            0,
            date(year=2018, month=1, day=1),
            date(year=2018, month=12, day=31),
            Decimal(0),
        ),
        (
            # Rent adjustment
            RentAdjustmentType.DISCOUNT,
            date(year=2018, month=1, day=1),
            date(year=2018, month=12, day=31),
            RentAdjustmentAmountType.PERCENT_PER_YEAR,
            50,
            # Fixed initial year rent
            0,
            date(year=2018, month=1, day=1),
            date(year=2018, month=12, day=31),
            Decimal(0),
        ),
        (
            # Rent adjustment
            RentAdjustmentType.INCREASE,
            date(year=2018, month=1, day=1),
            date(year=2018, month=12, day=31),
            RentAdjustmentAmountType.PERCENT_PER_YEAR,
            50,
            # Fixed initial year rent
            0,
            date(year=2018, month=1, day=1),
            date(year=2018, month=12, day=31),
            Decimal(0),
        ),
        (
            # Rent adjustment
            RentAdjustmentType.DISCOUNT,
            date(year=2018, month=1, day=1),
            date(year=2018, month=12, day=31),
            RentAdjustmentAmountType.PERCENT_PER_YEAR,
            0,
            # Fixed initial year rent
            0,
            date(year=2017, month=1, day=1),
            date(year=2017, month=1, day=1),
            Decimal(1927),
        ),
        (
            # Rent adjustment
            RentAdjustmentType.DISCOUNT,
            date(year=2018, month=1, day=1),
            date(year=2018, month=12, day=31),
            RentAdjustmentAmountType.PERCENT_PER_YEAR,
            0,
            # Fixed initial year rent
            100,
            date(year=2017, month=1, day=1),
            date(year=2017, month=1, day=1),
            Decimal(1927),
        ),
        (
            # Rent adjustment
            RentAdjustmentType.DISCOUNT,
            date(year=2018, month=1, day=1),
            date(year=2018, month=12, day=31),
            RentAdjustmentAmountType.PERCENT_PER_YEAR,
            0,
            # Fixed initial year rent
            100,
            date(year=2017, month=1, day=1),
            date(year=2018, month=3, day=31),
            Decimal("1470.25"),
        ),
        (
            # Rent adjustment
            RentAdjustmentType.DISCOUNT,
            date(year=2018, month=1, day=1),
            date(year=2018, month=12, day=31),
            RentAdjustmentAmountType.PERCENT_PER_YEAR,
            50,
            # Fixed initial year rent
            100,
            date(year=2018, month=1, day=1),
            date(year=2018, month=12, day=31),
            Decimal(50),
        ),
        (
            # Rent adjustment
            RentAdjustmentType.DISCOUNT,
            date(year=2018, month=1, day=1),
            date(year=2018, month=6, day=30),
            RentAdjustmentAmountType.PERCENT_PER_YEAR,
            100,
            # Fixed initial year rent
            100,
            date(year=2018, month=1, day=1),
            date(year=2018, month=12, day=31),
            Decimal(50),
        ),
        (
            # Rent adjustment
            RentAdjustmentType.DISCOUNT,
            date(year=2018, month=1, day=1),
            date(year=2018, month=6, day=30),
            RentAdjustmentAmountType.PERCENT_PER_YEAR,
            50,
            # Fixed initial year rent
            100,
            date(year=2018, month=7, day=1),
            date(year=2018, month=12, day=31),
            Decimal("531.75"),
        ),
        (
            # Rent adjustment
            RentAdjustmentType.DISCOUNT,
            date(year=2018, month=1, day=1),
            date(year=2018, month=6, day=30),
            RentAdjustmentAmountType.PERCENT_PER_YEAR,
            100,
            # Fixed initial year rent
            100,
            date(year=2018, month=7, day=1),
            date(year=2018, month=12, day=31),
            Decimal(50),
        ),
        (
            # Rent adjustment
            RentAdjustmentType.DISCOUNT,
            date(year=2018, month=6, day=1),
            date(year=2018, month=6, day=30),
            RentAdjustmentAmountType.PERCENT_PER_YEAR,
            100,
            # Fixed initial year rent
            100,
            date(year=2018, month=1, day=1),
            date(year=2018, month=12, day=31),
            pytest.approx(Decimal("91.6666")),
        ),
        (
            # Rent adjustment
            RentAdjustmentType.DISCOUNT,
            date(year=2018, month=6, day=1),
            date(year=2018, month=6, day=30),
            RentAdjustmentAmountType.PERCENT_PER_YEAR,
            50,
            # Fixed initial year rent
            100,
            date(year=2017, month=1, day=1),
            date(year=2017, month=12, day=31),
            pytest.approx(Decimal("1846.708")),
        ),
    ],
)
def test_get_amount_for_date_range_contract_with_adjustment_and_fixed_initial(
    lease_test_data,
    rent_factory,
    contract_rent_factory,
    rent_adjustment_factory,
    adjustment_type,
    adjustment_start_date,
    adjustment_end_date,
    adjustment_amount_type,
    adjustment_amount,
    fixed_initial_year_rent_factory,
    fixed_initial_amount,
    fixed_initial_start_date,
    fixed_initial_end_date,
    expected,
):

    lease = lease_test_data["lease"]

    rent = rent_factory(
        lease=lease,
        cycle=RentCycle.JANUARY_TO_DECEMBER,
        due_dates_type=DueDatesType.FIXED,
        due_dates_per_year=1,
    )

    contract_rent = contract_rent_factory(
        rent=rent,
        intended_use_id=1,
        amount=Decimal(100),
        period=PeriodType.PER_YEAR,
        base_amount=Decimal(100),
        base_amount_period=PeriodType.PER_YEAR,
    )

    rent_adjustment_factory(
        rent=rent,
        intended_use=contract_rent.intended_use,
        type=adjustment_type,
        start_date=adjustment_start_date,
        end_date=adjustment_end_date,
        amount_type=adjustment_amount_type,
        full_amount=adjustment_amount,
    )

    fixed_initial_year_rent_factory(
        rent=rent,
        intended_use=contract_rent.intended_use,
        amount=fixed_initial_amount,
        start_date=fixed_initial_start_date,
        end_date=fixed_initial_end_date,
    )

    range_start = date(year=2018, month=1, day=1)
    range_end = date(year=2018, month=12, day=31)

    calculation_result = rent.get_amount_for_date_range(range_start, range_end)
    assert calculation_result.get_total_amount() == expected


@pytest.mark.django_db
@pytest.mark.parametrize(
    "amount1, period1, start_date1, end_date1, amount2, period2, start_date2, end_date2, expected",
    [
        (
            Decimal(0),
            PeriodType.PER_YEAR,
            None,
            None,
            Decimal(0),
            PeriodType.PER_YEAR,
            None,
            None,
            Decimal(0),
        ),
        (
            Decimal(0),
            PeriodType.PER_YEAR,
            date(year=2016, month=1, day=1),
            date(year=2016, month=12, day=31),
            Decimal(0),
            PeriodType.PER_YEAR,
            date(year=2020, month=1, day=1),
            date(year=2020, month=12, day=31),
            Decimal(0),
        ),
        (
            Decimal(100),
            PeriodType.PER_YEAR,
            date(year=2020, month=1, day=1),
            date(year=2020, month=12, day=31),
            Decimal(100),
            PeriodType.PER_YEAR,
            None,
            None,
            Decimal(1927),
        ),
        (
            Decimal(100),
            PeriodType.PER_YEAR,
            date(year=2017, month=1, day=1),
            date(year=2017, month=12, day=31),
            Decimal(100),
            PeriodType.PER_YEAR,
            None,
            None,
            Decimal(1927),
        ),
        (
            Decimal(100),
            PeriodType.PER_YEAR,
            None,
            None,
            Decimal(100),
            PeriodType.PER_YEAR,
            date(year=2020, month=1, day=1),
            date(year=2020, month=12, day=31),
            Decimal(1927),
        ),
        (
            Decimal(100),
            PeriodType.PER_YEAR,
            None,
            None,
            Decimal(100),
            PeriodType.PER_YEAR,
            date(year=2017, month=1, day=1),
            date(year=2017, month=12, day=31),
            Decimal(1927),
        ),
        (
            Decimal(100),
            PeriodType.PER_YEAR,
            date(year=2018, month=1, day=1),
            date(year=2018, month=12, day=31),
            Decimal(100),
            PeriodType.PER_YEAR,
            date(year=2018, month=1, day=1),
            date(year=2018, month=12, day=31),
            Decimal(3854),
        ),
        (
            Decimal(100),
            PeriodType.PER_YEAR,
            date(year=2018, month=1, day=1),
            date(year=2018, month=6, day=30),
            Decimal(100),
            PeriodType.PER_YEAR,
            date(year=2018, month=7, day=1),
            date(year=2018, month=12, day=31),
            Decimal(1927),
        ),
    ],
)
def test_get_amount_for_date_range_two_contracts(
    lease_test_data,
    rent_factory,
    contract_rent_factory,
    amount1,
    period1,
    start_date1,
    end_date1,
    amount2,
    period2,
    start_date2,
    end_date2,
    expected,
):
    lease = lease_test_data["lease"]

    rent = rent_factory(
        lease=lease,
        cycle=RentCycle.JANUARY_TO_DECEMBER,
        due_dates_type=DueDatesType.FIXED,
        due_dates_per_year=1,
    )

    contract_rent_factory(
        rent=rent,
        intended_use_id=1,
        amount=amount1,
        period=period1,
        base_amount=amount1,
        base_amount_period=period1,
        start_date=start_date1,
        end_date=end_date1,
    )

    contract_rent_factory(
        rent=rent,
        intended_use_id=1,
        amount=amount2,
        period=period2,
        base_amount=amount2,
        base_amount_period=period2,
        start_date=start_date2,
        end_date=end_date2,
    )

    range_start = date(year=2018, month=1, day=1)
    range_end = date(year=2018, month=12, day=31)

    calculation_result = rent.get_amount_for_date_range(range_start, range_end)
    assert calculation_result.get_total_amount() == expected


@pytest.mark.django_db
@pytest.mark.parametrize(
    "intended_use1, amount1, period1, start_date1, end_date1, intended_use2, amount2, period2, start_date2, end_date2, "
    "adjustment_type, adjustment_intended_use, adjustment_start_date, adjustment_end_date, adjustment_amount_type, "
    "adjustment_amount, expected",
    [
        (
            # Contract rent 1
            1,
            Decimal(0),
            PeriodType.PER_YEAR,
            None,
            None,
            # Contract rent 2
            1,
            Decimal(0),
            PeriodType.PER_YEAR,
            None,
            None,
            # Adjustment
            RentAdjustmentType.DISCOUNT,
            1,
            None,
            None,
            RentAdjustmentAmountType.PERCENT_PER_YEAR,
            Decimal(0),
            # Expected
            Decimal(0),
        ),
        (
            # Contract rent 1
            1,
            Decimal(0),
            PeriodType.PER_YEAR,
            None,
            None,
            # Contract rent 2
            1,
            Decimal(0),
            PeriodType.PER_YEAR,
            None,
            None,
            # Adjustment
            RentAdjustmentType.INCREASE,
            1,
            None,
            None,
            RentAdjustmentAmountType.PERCENT_PER_YEAR,
            Decimal(0),
            # Expected
            Decimal(0),
        ),
        (
            # Contract rent 1
            1,
            Decimal(100),
            PeriodType.PER_YEAR,
            None,
            None,
            # Contract rent 2
            1,
            Decimal(0),
            PeriodType.PER_YEAR,
            None,
            None,
            # Adjustment
            RentAdjustmentType.DISCOUNT,
            1,
            None,
            None,
            RentAdjustmentAmountType.PERCENT_PER_YEAR,
            Decimal(0),
            # Expected
            Decimal(1927),
        ),
        (
            # Contract rent 1
            1,
            Decimal(100),
            PeriodType.PER_YEAR,
            None,
            None,
            # Contract rent 2
            1,
            Decimal(0),
            PeriodType.PER_YEAR,
            None,
            None,
            # Adjustment
            RentAdjustmentType.INCREASE,
            1,
            None,
            None,
            RentAdjustmentAmountType.PERCENT_PER_YEAR,
            Decimal(0),
            # Expected
            Decimal(1927),
        ),
        (
            # Contract rent 1
            1,
            Decimal(100),
            PeriodType.PER_YEAR,
            None,
            None,
            # Contract rent 2
            1,
            Decimal(100),
            PeriodType.PER_YEAR,
            None,
            None,
            # Adjustment
            RentAdjustmentType.DISCOUNT,
            1,
            None,
            None,
            RentAdjustmentAmountType.PERCENT_PER_YEAR,
            Decimal(0),
            # Expected
            Decimal(3854),
        ),
        (
            # Contract rent 1
            1,
            Decimal(100),
            PeriodType.PER_YEAR,
            None,
            None,
            # Contract rent 2
            1,
            Decimal(100),
            PeriodType.PER_YEAR,
            None,
            None,
            # Adjustment
            RentAdjustmentType.INCREASE,
            1,
            None,
            None,
            RentAdjustmentAmountType.PERCENT_PER_YEAR,
            Decimal(0),
            # Expected
            Decimal(3854),
        ),
        (
            # Contract rent 1
            1,
            Decimal(100),
            PeriodType.PER_YEAR,
            None,
            None,
            # Contract rent 2
            2,
            Decimal(100),
            PeriodType.PER_YEAR,
            None,
            None,
            # Adjustment
            RentAdjustmentType.DISCOUNT,
            1,
            None,
            None,
            RentAdjustmentAmountType.PERCENT_PER_YEAR,
            Decimal(0),
            # Expected
            Decimal(3854),
        ),
        (
            # Contract rent 1
            1,
            Decimal(100),
            PeriodType.PER_YEAR,
            None,
            None,
            # Contract rent 2
            2,
            Decimal(100),
            PeriodType.PER_YEAR,
            None,
            None,
            # Adjustment
            RentAdjustmentType.INCREASE,
            1,
            None,
            None,
            RentAdjustmentAmountType.PERCENT_PER_YEAR,
            Decimal(0),
            # Expected
            Decimal(3854),
        ),
        (
            # Contract rent 1
            1,
            Decimal(100),
            PeriodType.PER_YEAR,
            None,
            None,
            # Contract rent 2
            1,
            Decimal(100),
            PeriodType.PER_YEAR,
            None,
            None,
            # Adjustment
            RentAdjustmentType.DISCOUNT,
            1,
            None,
            None,
            RentAdjustmentAmountType.PERCENT_PER_YEAR,
            Decimal(50),
            # Expected
            Decimal(1927),
        ),
        (
            # Contract rent 1
            1,
            Decimal(100),
            PeriodType.PER_YEAR,
            None,
            None,
            # Contract rent 2
            2,
            Decimal(100),
            PeriodType.PER_YEAR,
            None,
            None,
            # Adjustment
            RentAdjustmentType.DISCOUNT,
            3,
            None,
            None,
            RentAdjustmentAmountType.PERCENT_PER_YEAR,
            Decimal(50),
            # Expected
            Decimal(3854),
        ),
        (
            # Contract rent 1
            1,
            Decimal(100),
            PeriodType.PER_YEAR,
            None,
            None,
            # Contract rent 2
            2,
            Decimal(100),
            PeriodType.PER_YEAR,
            None,
            None,
            # Adjustment
            RentAdjustmentType.INCREASE,
            3,
            None,
            None,
            RentAdjustmentAmountType.PERCENT_PER_YEAR,
            Decimal(50),
            # Expected
            Decimal(3854),
        ),
        (
            # Contract rent 1
            1,
            Decimal(100),
            PeriodType.PER_YEAR,
            None,
            None,
            # Contract rent 2
            2,
            Decimal(100),
            PeriodType.PER_YEAR,
            None,
            None,
            # Adjustment
            RentAdjustmentType.DISCOUNT,
            1,
            None,
            None,
            RentAdjustmentAmountType.PERCENT_PER_YEAR,
            Decimal(50),
            # Expected
            Decimal("2890.5"),
        ),
        (
            # Contract rent 1
            1,
            Decimal(100),
            PeriodType.PER_YEAR,
            None,
            None,
            # Contract rent 2
            2,
            Decimal(100),
            PeriodType.PER_YEAR,
            None,
            None,
            # Adjustment
            RentAdjustmentType.INCREASE,
            1,
            None,
            None,
            RentAdjustmentAmountType.PERCENT_PER_YEAR,
            Decimal(50),
            # Expected
            Decimal("4817.5"),
        ),
        (
            # Contract rent 1
            1,
            Decimal(100),
            PeriodType.PER_YEAR,
            None,
            None,
            # Contract rent 2
            2,
            Decimal(100),
            PeriodType.PER_YEAR,
            None,
            None,
            # Adjustment
            RentAdjustmentType.DISCOUNT,
            2,
            None,
            None,
            RentAdjustmentAmountType.PERCENT_PER_YEAR,
            Decimal(50),
            # Expected
            Decimal("2890.5"),
        ),
        (
            # Contract rent 1
            1,
            Decimal(100),
            PeriodType.PER_YEAR,
            None,
            None,
            # Contract rent 2
            2,
            Decimal(100),
            PeriodType.PER_YEAR,
            None,
            None,
            # Adjustment
            RentAdjustmentType.INCREASE,
            2,
            None,
            None,
            RentAdjustmentAmountType.PERCENT_PER_YEAR,
            Decimal(50),
            # Expected
            Decimal("4817.5"),
        ),
        (
            # Contract rent 1
            1,
            Decimal(100),
            PeriodType.PER_YEAR,
            date(year=2018, month=1, day=1),
            date(year=2018, month=6, day=30),
            # Contract rent 2
            1,
            Decimal(100),
            PeriodType.PER_YEAR,
            date(year=2018, month=7, day=1),
            date(year=2018, month=12, day=31),
            # Adjustment
            RentAdjustmentType.DISCOUNT,
            1,
            None,
            None,
            RentAdjustmentAmountType.PERCENT_PER_YEAR,
            Decimal(50),
            # Expected
            Decimal("963.5"),
        ),
        (
            # Contract rent 1
            1,
            Decimal(100),
            PeriodType.PER_YEAR,
            date(year=2018, month=1, day=1),
            date(year=2018, month=6, day=30),
            # Contract rent 2
            1,
            Decimal(100),
            PeriodType.PER_YEAR,
            date(year=2018, month=7, day=1),
            date(year=2018, month=12, day=31),
            # Adjustment
            RentAdjustmentType.INCREASE,
            1,
            None,
            None,
            RentAdjustmentAmountType.PERCENT_PER_YEAR,
            Decimal(50),
            # Expected
            Decimal("2890.5"),
        ),
        (
            # Contract rent 1
            1,
            Decimal(150),
            PeriodType.PER_YEAR,
            date(year=2018, month=1, day=1),
            date(year=2018, month=6, day=30),
            # Contract rent 2
            1,
            Decimal(50),
            PeriodType.PER_YEAR,
            date(year=2018, month=7, day=1),
            date(year=2018, month=12, day=31),
            # Adjustment
            RentAdjustmentType.DISCOUNT,
            1,
            date(year=2018, month=4, day=1),
            date(year=2018, month=6, day=30),
            RentAdjustmentAmountType.PERCENT_PER_YEAR,
            Decimal(100),
            # Expected
            Decimal("1204.375"),
        ),
        (
            # Contract rent 1
            1,
            Decimal(150),
            PeriodType.PER_YEAR,
            date(year=2018, month=1, day=1),
            date(year=2018, month=6, day=30),
            # Contract rent 2
            1,
            Decimal(50),
            PeriodType.PER_YEAR,
            date(year=2018, month=7, day=1),
            date(year=2018, month=12, day=31),
            # Adjustment
            RentAdjustmentType.INCREASE,
            1,
            date(year=2018, month=4, day=1),
            date(year=2018, month=6, day=30),
            RentAdjustmentAmountType.PERCENT_PER_YEAR,
            Decimal(100),
            # Expected
            Decimal("2649.625"),
        ),
        (
            # Contract rent 1
            1,
            Decimal(150),
            PeriodType.PER_YEAR,
            date(year=2018, month=1, day=1),
            date(year=2018, month=6, day=30),
            # Contract rent 2
            1,
            Decimal(50),
            PeriodType.PER_YEAR,
            date(year=2018, month=7, day=1),
            date(year=2018, month=12, day=31),
            # Adjustment
            RentAdjustmentType.DISCOUNT,
            1,
            date(year=2018, month=4, day=1),
            date(year=2018, month=6, day=30),
            RentAdjustmentAmountType.AMOUNT_PER_YEAR,
            Decimal(1200),
            # Expected
            Decimal("1627"),
        ),
        (
            # Contract rent 1
            1,
            Decimal(150),
            PeriodType.PER_YEAR,
            date(year=2018, month=1, day=1),
            date(year=2018, month=6, day=30),
            # Contract rent 2
            1,
            Decimal(50),
            PeriodType.PER_YEAR,
            date(year=2018, month=7, day=1),
            date(year=2018, month=12, day=31),
            # Adjustment
            RentAdjustmentType.INCREASE,
            1,
            date(year=2018, month=4, day=1),
            date(year=2018, month=6, day=30),
            RentAdjustmentAmountType.AMOUNT_PER_YEAR,
            Decimal(1200),
            # Expected
            Decimal("2227"),
        ),
    ],
)
def test_get_amount_for_date_range_two_contracts_with_adjustment(
    lease_test_data,
    rent_factory,
    contract_rent_factory,
    rent_adjustment_factory,
    intended_use1,
    amount1,
    period1,
    start_date1,
    end_date1,
    intended_use2,
    amount2,
    period2,
    start_date2,
    end_date2,
    adjustment_type,
    adjustment_intended_use,
    adjustment_start_date,
    adjustment_end_date,
    adjustment_amount_type,
    adjustment_amount,
    expected,
):
    lease = lease_test_data["lease"]

    rent = rent_factory(
        lease=lease,
        cycle=RentCycle.JANUARY_TO_DECEMBER,
        due_dates_type=DueDatesType.FIXED,
        due_dates_per_year=1,
    )

    contract_rent_factory(
        rent=rent,
        intended_use_id=intended_use1,
        amount=amount1,
        period=period1,
        base_amount=amount1,
        base_amount_period=period1,
        start_date=start_date1,
        end_date=end_date1,
    )

    contract_rent_factory(
        rent=rent,
        intended_use_id=intended_use2,
        amount=amount2,
        period=period2,
        base_amount=amount2,
        base_amount_period=period2,
        start_date=start_date2,
        end_date=end_date2,
    )

    rent_adjustment_factory(
        rent=rent,
        intended_use_id=adjustment_intended_use,
        type=adjustment_type,
        start_date=adjustment_start_date,
        end_date=adjustment_end_date,
        amount_type=adjustment_amount_type,
        full_amount=adjustment_amount,
    )

    range_start = date(year=2018, month=1, day=1)
    range_end = date(year=2018, month=12, day=31)

    calculation_result = rent.get_amount_for_date_range(range_start, range_end)
    assert calculation_result.get_total_amount() == expected


@pytest.mark.django_db
@pytest.mark.parametrize(
    "dry_run, adjustment_type, adjustment_amount, expected_rent, expected_amount_left",
    [
        # Save amount left
        # Discount
        (False, RentAdjustmentType.DISCOUNT, 100, Decimal(1827), Decimal(0)),
        (False, RentAdjustmentType.DISCOUNT, 10000, Decimal(0), Decimal(8073)),
        # Increase
        (False, RentAdjustmentType.INCREASE, 100, Decimal(2027), Decimal(0)),
        (False, RentAdjustmentType.INCREASE, 10000, Decimal(11927), Decimal(0)),
        # Don't save amount left
        # Discount
        (True, RentAdjustmentType.DISCOUNT, 100, Decimal(1827), Decimal(100)),
        (True, RentAdjustmentType.DISCOUNT, 10000, Decimal(0), Decimal(10000)),
        # Increase
        (True, RentAdjustmentType.INCREASE, 100, Decimal(2027), Decimal(100)),
        (True, RentAdjustmentType.INCREASE, 10000, Decimal(11927), Decimal(10000)),
    ],
)
def test_adjustment_type_amount_total(
    lease_test_data,
    rent_factory,
    contract_rent_factory,
    rent_adjustment_factory,
    dry_run,
    adjustment_type,
    adjustment_amount,
    expected_rent,
    expected_amount_left,
):
    lease = lease_test_data["lease"]

    rent = rent_factory(
        lease=lease,
        cycle=RentCycle.JANUARY_TO_DECEMBER,
        due_dates_type=DueDatesType.FIXED,
        due_dates_per_year=1,
    )

    contract_rent = contract_rent_factory(
        rent=rent,
        intended_use_id=1,
        amount=Decimal(100),
        period=PeriodType.PER_YEAR,
        base_amount=Decimal(100),
        base_amount_period=PeriodType.PER_YEAR,
    )

    rent_adjustment = rent_adjustment_factory(
        rent=rent,
        intended_use=contract_rent.intended_use,
        type=adjustment_type,
        start_date=None,
        end_date=None,
        amount_type=RentAdjustmentAmountType.AMOUNT_TOTAL,
        full_amount=adjustment_amount,
        amount_left=adjustment_amount,
    )

    range_start = date(year=2018, month=1, day=1)
    range_end = date(year=2018, month=12, day=31)

    calculation_result = rent.get_amount_for_date_range(
        range_start, range_end, dry_run=dry_run
    )
    assert calculation_result.get_total_amount() == expected_rent

    rent_adjustment = RentAdjustment.objects.get(pk=rent_adjustment.id)
    assert rent_adjustment.amount_left == expected_amount_left


@pytest.mark.django_db
@pytest.mark.parametrize(
    "adjustment_start_date1, adjustment_end_date1, adjustment_type1, adjustment_amount1, "
    "adjustment_start_date2, adjustment_end_date2, adjustment_type2, adjustment_amount2, expected",
    [
        (
            date(year=2018, month=1, day=1),  # Adjustment 1 start date
            date(year=2018, month=6, day=30),  # Adjustment 1 end date
            RentAdjustmentType.DISCOUNT,  # Adjustment 1 type
            50,  # Adjustment 1 amount
            date(year=2018, month=7, day=1),  # Adjustment 2 start date
            date(year=2018, month=12, day=31),  # Adjustment 2 end date
            RentAdjustmentType.DISCOUNT,  # Adjustment 2 type
            50,  # Adjustment 2 amount
            Decimal(600),
        ),
        (
            date(year=2018, month=1, day=1),  # Adjustment 1 start date
            date(year=2018, month=12, day=31),  # Adjustment 1 end date
            RentAdjustmentType.DISCOUNT,  # Adjustment 1 type
            50,  # Adjustment 1 amount
            date(year=2018, month=1, day=1),  # Adjustment 2 start date
            date(year=2018, month=12, day=31),  # Adjustment 2 end date
            RentAdjustmentType.DISCOUNT,  # Adjustment 2 type
            50,  # Adjustment 2 amount
            Decimal(300),
        ),
        (
            date(year=2018, month=3, day=1),  # Adjustment 1 start date
            date(year=2018, month=8, day=31),  # Adjustment 1 end date
            RentAdjustmentType.DISCOUNT,  # Adjustment 1 type
            50,  # Adjustment 1 amount
            date(year=2018, month=5, day=1),  # Adjustment 2 start date
            date(year=2018, month=10, day=31),  # Adjustment 2 end date
            RentAdjustmentType.DISCOUNT,  # Adjustment 2 type
            50,  # Adjustment 2 amount
            Decimal(700),
        ),
    ],
)
def test_get_amount_for_date_range_adjustments_two_in_series(
    lease_test_data,
    rent_factory,
    contract_rent_factory,
    rent_adjustment_factory,
    adjustment_start_date1,
    adjustment_end_date1,
    adjustment_type1,
    adjustment_amount1,
    adjustment_start_date2,
    adjustment_end_date2,
    adjustment_type2,
    adjustment_amount2,
    expected,
):

    lease = lease_test_data["lease"]

    rent = rent_factory(
        lease=lease,
        type=RentType.FIXED,
        cycle=RentCycle.JANUARY_TO_DECEMBER,
        due_dates_type=DueDatesType.FIXED,
        due_dates_per_year=1,
    )

    contract_rent = contract_rent_factory(
        rent=rent,
        intended_use_id=1,
        amount=Decimal(1200),
        period=PeriodType.PER_YEAR,
        base_amount=Decimal(100),
        base_amount_period=PeriodType.PER_YEAR,
    )

    rent_adjustment_factory(
        rent=rent,
        intended_use=contract_rent.intended_use,
        type=adjustment_type1,
        start_date=adjustment_start_date1,
        end_date=adjustment_end_date1,
        amount_type=RentAdjustmentAmountType.PERCENT_PER_YEAR,
        full_amount=adjustment_amount1,
    )

    rent_adjustment_factory(
        rent=rent,
        intended_use=contract_rent.intended_use,
        type=adjustment_type2,
        start_date=adjustment_start_date2,
        end_date=adjustment_end_date2,
        amount_type=RentAdjustmentAmountType.PERCENT_PER_YEAR,
        full_amount=adjustment_amount2,
    )

    range_start = date(year=2018, month=1, day=1)
    range_end = date(year=2018, month=12, day=31)

    calculation_result = rent.get_amount_for_date_range(range_start, range_end)
    assert calculation_result.get_total_amount() == expected


@pytest.mark.django_db
@pytest.mark.parametrize(
    "adjustment_start_date1, adjustment_end_date1, adjustment_type1, adjustment_amount1, "
    "adjustment_start_date2, adjustment_end_date2, adjustment_type2, adjustment_amount2, expected",
    [
        (
            date(year=2018, month=1, day=1),  # Adjustment 1 start date
            date(year=2018, month=6, day=30),  # Adjustment 1 end date
            RentAdjustmentType.DISCOUNT,  # Adjustment 1 type
            50,  # Adjustment 1 amount
            date(year=2018, month=7, day=1),  # Adjustment 2 start date
            date(year=2018, month=12, day=31),  # Adjustment 2 end date
            RentAdjustmentType.DISCOUNT,  # Adjustment 2 type
            50,  # Adjustment 2 amount
            Decimal(600),
        ),
        (
            date(year=2018, month=1, day=1),  # Adjustment 1 start date
            date(year=2018, month=12, day=31),  # Adjustment 1 end date
            RentAdjustmentType.DISCOUNT,  # Adjustment 1 type
            50,  # Adjustment 1 amount
            date(year=2018, month=1, day=1),  # Adjustment 2 start date
            date(year=2018, month=12, day=31),  # Adjustment 2 end date
            RentAdjustmentType.DISCOUNT,  # Adjustment 2 type
            50,  # Adjustment 2 amount
            Decimal(300),
        ),
        (
            date(year=2018, month=3, day=1),  # Adjustment 1 start date
            date(year=2018, month=8, day=31),  # Adjustment 1 end date
            RentAdjustmentType.DISCOUNT,  # Adjustment 1 type
            50,  # Adjustment 1 amount
            date(year=2018, month=5, day=1),  # Adjustment 2 start date
            date(year=2018, month=10, day=31),  # Adjustment 2 end date
            RentAdjustmentType.DISCOUNT,  # Adjustment 2 type
            50,  # Adjustment 2 amount
            Decimal(700),
        ),
    ],
)
def test_get_amount_for_date_range_adjustments_two_in_series_fixed_initial_year_rent(
    lease_test_data,
    rent_factory,
    contract_rent_factory,
    fixed_initial_year_rent_factory,
    rent_adjustment_factory,
    adjustment_start_date1,
    adjustment_end_date1,
    adjustment_type1,
    adjustment_amount1,
    adjustment_start_date2,
    adjustment_end_date2,
    adjustment_type2,
    adjustment_amount2,
    expected,
):

    lease = lease_test_data["lease"]

    rent = rent_factory(
        lease=lease,
        type=RentType.FIXED,
        cycle=RentCycle.JANUARY_TO_DECEMBER,
        due_dates_type=DueDatesType.FIXED,
        due_dates_per_year=1,
    )

    fixed_initial_year_rent = fixed_initial_year_rent_factory(
        rent=rent, intended_use_id=1, amount=Decimal(1200)
    )

    rent_adjustment_factory(
        rent=rent,
        intended_use=fixed_initial_year_rent.intended_use,
        type=adjustment_type1,
        start_date=adjustment_start_date1,
        end_date=adjustment_end_date1,
        amount_type=RentAdjustmentAmountType.PERCENT_PER_YEAR,
        full_amount=adjustment_amount1,
    )

    rent_adjustment_factory(
        rent=rent,
        intended_use=fixed_initial_year_rent.intended_use,
        type=adjustment_type2,
        start_date=adjustment_start_date2,
        end_date=adjustment_end_date2,
        amount_type=RentAdjustmentAmountType.PERCENT_PER_YEAR,
        full_amount=adjustment_amount2,
    )

    range_start = date(year=2018, month=1, day=1)
    range_end = date(year=2018, month=12, day=31)

    calculation_result = rent.get_amount_for_date_range(range_start, range_end)
    assert calculation_result.get_total_amount() == expected


@pytest.mark.django_db
@pytest.mark.parametrize(
    "adjustment_start_date1, adjustment_end_date1, adjustment_type1, adjustment_amount1, expected",
    [
        (
            date(year=2018, month=1, day=1),
            date(year=2018, month=6, day=30),
            RentAdjustmentType.DISCOUNT,
            50,
            Decimal(900),
        )
    ],
)
def test_fixed_initial_year_rent_amount_for_date_range(
    lease_test_data,
    rent_factory,
    fixed_initial_year_rent_factory,
    rent_adjustment_factory,
    adjustment_start_date1,
    adjustment_end_date1,
    adjustment_type1,
    adjustment_amount1,
    expected,
):

    lease = lease_test_data["lease"]

    rent = rent_factory(
        lease=lease,
        type=RentType.FIXED,
        cycle=RentCycle.JANUARY_TO_DECEMBER,
        due_dates_type=DueDatesType.FIXED,
        due_dates_per_year=1,
    )

    fixed_initial_year_rent = fixed_initial_year_rent_factory(
        rent=rent,
        intended_use_id=1,
        start_date=date(year=2018, month=1, day=1),
        end_date=date(year=2018, month=12, day=31),
        amount=Decimal(1200),
    )

    rent_adjustment_factory(
        rent=rent,
        intended_use=fixed_initial_year_rent.intended_use,
        type=adjustment_type1,
        start_date=adjustment_start_date1,
        end_date=adjustment_end_date1,
        amount_type=RentAdjustmentAmountType.PERCENT_PER_YEAR,
        full_amount=adjustment_amount1,
    )

    range_start = date(year=2018, month=1, day=1)
    range_end = date(year=2018, month=12, day=31)

    calculation_result = rent.fixed_initial_year_rent_amount_for_date_range(
        fixed_initial_year_rent.intended_use, range_start, range_end
    )
    assert calculation_result.get_total_amount() == expected


@pytest.mark.django_db
@pytest.mark.parametrize(
    "rent_start_date, rent_end_date, period_start_date, period_end_date, expected",
    [
        (None, None, None, None, True),
        (
            None,
            None,
            date(year=1990, month=1, day=1),
            date(year=1990, month=1, day=1),
            True,
        ),
        (
            None,
            None,
            date(year=2017, month=1, day=1),
            date(year=2019, month=12, day=31),
            True,
        ),
        (
            date(year=2017, month=1, day=1),
            date(year=2019, month=12, day=31),
            date(year=2017, month=1, day=1),
            date(year=2019, month=12, day=31),
            True,
        ),
        (
            date(year=2000, month=1, day=1),
            date(year=2000, month=12, day=31),
            date(year=1990, month=1, day=1),
            date(year=2020, month=1, day=1),
            True,
        ),
        (
            date(year=1990, month=1, day=1),
            date(year=2020, month=1, day=1),
            date(year=2000, month=1, day=1),
            date(year=2000, month=12, day=31),
            True,
        ),
        (
            date(year=2000, month=1, day=1),
            date(year=2000, month=12, day=31),
            date(year=1999, month=12, day=15),
            date(year=2000, month=1, day=15),
            True,
        ),
        (
            date(year=2000, month=1, day=1),
            date(year=2000, month=12, day=31),
            date(year=2000, month=1, day=15),
            date(year=2000, month=2, day=15),
            True,
        ),
        (
            date(year=2017, month=1, day=1),
            date(year=2019, month=12, day=31),
            date(year=2020, month=1, day=1),
            date(year=2020, month=12, day=31),
            False,
        ),
        (
            date(year=1990, month=1, day=1),
            date(year=1990, month=1, day=1),
            date(year=2020, month=1, day=1),
            date(year=2020, month=12, day=31),
            False,
        ),
        (
            date(year=1990, month=1, day=1),
            date(year=1990, month=1, day=1),
            date(year=1990, month=1, day=2),
            date(year=1990, month=1, day=2),
            False,
        ),
    ],
)
def test_is_active_in_period(
    lease_test_data,
    rent_factory,
    rent_start_date,
    rent_end_date,
    period_start_date,
    period_end_date,
    expected,
):
    lease = lease_test_data["lease"]

    rent = rent_factory(
        lease=lease,
        cycle=RentCycle.JANUARY_TO_DECEMBER,
        due_dates_type=DueDatesType.FIXED,
        due_dates_per_year=1,
        start_date=rent_start_date,
        end_date=rent_end_date,
    )

    assert rent.is_active_in_period(period_start_date, period_end_date) == expected


@pytest.mark.django_db
@pytest.mark.parametrize(
    "start_date1, end_date1, start_date2, end_date2, expected",
    [
        (
            date(year=2017, month=1, day=1),
            date(year=2019, month=12, day=31),
            date(year=2017, month=1, day=1),
            date(year=2019, month=12, day=31),
            [],
        ),
        (
            date(year=2017, month=1, day=1),
            date(year=2017, month=12, day=31),
            date(year=2018, month=1, day=1),
            date(year=2018, month=3, day=31),
            [(date(2018, 4, 1), date(2018, 8, 31))],
        ),
        (
            date(year=2018, month=1, day=1),
            date(year=2018, month=3, day=31),
            date(year=2018, month=8, day=1),
            date(year=2018, month=12, day=31),
            [(date(2018, 4, 1), date(2018, 7, 31))],
        ),
        (
            date(year=2017, month=1, day=1),
            date(year=2018, month=6, day=30),
            date(year=2017, month=1, day=1),
            date(year=2018, month=6, day=30),
            [(date(2018, 7, 1), date(2018, 8, 31))],
        ),
        (
            date(year=2017, month=1, day=1),
            date(year=2017, month=1, day=1),
            date(year=2017, month=1, day=1),
            date(year=2017, month=1, day=1),
            [],
        ),
        (
            date(year=2019, month=1, day=1),
            date(year=2019, month=1, day=1),
            date(year=2019, month=1, day=1),
            date(year=2019, month=1, day=1),
            [],
        ),
        (
            date(year=2018, month=3, day=1),
            date(year=2018, month=3, day=31),
            date(year=2018, month=3, day=1),
            date(year=2018, month=3, day=31),
            [(date(2018, 4, 1), date(2018, 8, 31))],
        ),
    ],
)
def test_fixed_initial_year_rent_for_date_range_remaining_ranges(
    lease_test_data,
    rent_factory,
    contract_rent_factory,
    fixed_initial_year_rent_factory,
    start_date1,
    end_date1,
    start_date2,
    end_date2,
    expected,
):

    lease = lease_test_data["lease"]

    rent = rent_factory(
        lease=lease,
        cycle=RentCycle.JANUARY_TO_DECEMBER,
        due_dates_type=DueDatesType.FIXED,
        due_dates_per_year=1,
    )

    contract_rent = contract_rent_factory(
        rent=rent,
        intended_use_id=1,
        amount=Decimal(100),
        period=PeriodType.PER_YEAR,
        base_amount=Decimal(100),
        base_amount_period=PeriodType.PER_YEAR,
    )

    fixed_initial_year_rent_factory(
        rent=rent,
        intended_use=contract_rent.intended_use,
        amount=Decimal(100),
        start_date=start_date1,
        end_date=end_date1,
    )

    fixed_initial_year_rent_factory(
        rent=rent,
        intended_use=contract_rent.intended_use,
        amount=Decimal(100),
        start_date=start_date2,
        end_date=end_date2,
    )

    range_start = date(year=2018, month=3, day=1)
    range_end = date(year=2018, month=8, day=31)

    calculation_result = rent.fixed_initial_year_rent_amount_for_date_range(
        contract_rent.intended_use, range_start, range_end
    )
    assert calculation_result.remaining_ranges == expected


@pytest.mark.django_db
@pytest.mark.parametrize(
    "rent_cycle, due_dates_per_year, billing_period, expected",
    [
        (
            RentCycle.JANUARY_TO_DECEMBER,
            0,
            (date(year=2017, month=1, day=1), date(year=2017, month=6, day=1)),
            False,
        ),
        (
            RentCycle.JANUARY_TO_DECEMBER,
            1,
            (date(year=2017, month=1, day=1), date(year=2017, month=6, day=1)),
            False,
        ),
        (
            RentCycle.JANUARY_TO_DECEMBER,
            4,
            (date(year=2017, month=1, day=1), date(year=2017, month=6, day=1)),
            False,
        ),
        (
            RentCycle.JANUARY_TO_DECEMBER,
            12,
            (date(year=2017, month=1, day=1), date(year=2017, month=6, day=1)),
            False,
        ),
        (
            RentCycle.JANUARY_TO_DECEMBER,
            1,
            (date(year=2017, month=1, day=1), date(year=2017, month=12, day=31)),
            True,
        ),
        (
            RentCycle.JANUARY_TO_DECEMBER,
            2,
            (date(year=2017, month=1, day=1), date(year=2017, month=6, day=30)),
            False,
        ),
        (
            RentCycle.JANUARY_TO_DECEMBER,
            2,
            (date(year=2017, month=7, day=1), date(year=2017, month=12, day=31)),
            True,
        ),
        (
            RentCycle.APRIL_TO_MARCH,
            0,
            (date(year=2017, month=1, day=1), date(year=2017, month=6, day=1)),
            False,
        ),
        (
            RentCycle.APRIL_TO_MARCH,
            1,
            (date(year=2017, month=1, day=1), date(year=2017, month=6, day=1)),
            False,
        ),
        (
            RentCycle.APRIL_TO_MARCH,
            4,
            (date(year=2017, month=1, day=1), date(year=2017, month=6, day=1)),
            False,
        ),
        (
            RentCycle.APRIL_TO_MARCH,
            12,
            (date(year=2017, month=1, day=1), date(year=2017, month=6, day=1)),
            False,
        ),
        (
            RentCycle.APRIL_TO_MARCH,
            1,
            (date(year=2017, month=1, day=1), date(year=2017, month=12, day=31)),
            True,
        ),
        (
            RentCycle.APRIL_TO_MARCH,
            2,
            (date(year=2017, month=1, day=1), date(year=2017, month=6, day=30)),
            False,
        ),
        (
            RentCycle.APRIL_TO_MARCH,
            2,
            (date(year=2017, month=7, day=1), date(year=2017, month=12, day=31)),
            True,
        ),
    ],
)
def test_is_the_last_billing_period(
    lease_test_data,
    rent_factory,
    rent_cycle,
    due_dates_per_year,
    billing_period,
    expected,
):
    lease = lease_test_data["lease"]

    rent = rent_factory(lease=lease)
    rent.cycle = rent_cycle
    rent.start_date = date(year=2000, month=1, day=1)
    rent.end_date = date(year=2030, month=1, day=1)
    rent.due_dates_type = DueDatesType.FIXED
    rent.due_dates_per_year = due_dates_per_year
    rent.save()

    assert rent.is_the_last_billing_period(billing_period) == expected


@pytest.mark.django_db
def test_set_start_price_index_point_figure_without_index(rent_factory, lease_factory):
    """Periodic rent adjustment's point figure should not be set if the rent
    does not use periodic rent adjustment."""
    lease = lease_factory()
    rent: Rent = rent_factory(lease=lease)
    rent.set_start_price_index_point_figure()

    assert rent.start_price_index_point_figure_value is None
    assert rent.start_price_index_point_figure_year is None


@pytest.mark.django_db
def test_set_start_price_index_point_figure_values_already_set(
    rent_factory,
    lease_factory,
    old_dwellings_in_housing_companies_price_index_factory,
):
    """Periodic rent adjustment's point figure should not be changed if the
    details are already set."""
    lease = lease_factory(start_date=date(year=2024, month=1, day=1))
    old_dwellings_in_housing_companies_price_index = (
        old_dwellings_in_housing_companies_price_index_factory()
    )
    year_already_set = 2023
    value_already_set = 103
    rent: Rent = rent_factory(
        lease=lease,
        old_dwellings_in_housing_companies_price_index=old_dwellings_in_housing_companies_price_index,
        start_price_index_point_figure_year=year_already_set,
        start_price_index_point_figure_value=value_already_set,
    )
    rent.set_start_price_index_point_figure()

    assert rent.start_price_index_point_figure_year == year_already_set
    assert rent.start_price_index_point_figure_value == value_already_set


@pytest.mark.django_db
def test_set_start_price_index_point_figure_not_available(
    rent_factory,
    lease_factory,
    old_dwellings_in_housing_companies_price_index_factory,
    index_point_figure_yearly_factory,
):
    """Periodic rent adjustment's point figure should not be set if the desired
    point figure is not available."""
    lease = lease_factory(start_date=date(year=2024, month=1, day=1))
    old_dwellings_in_housing_companies_price_index = (
        old_dwellings_in_housing_companies_price_index_factory()
    )
    rent: Rent = rent_factory(
        lease=lease,
        old_dwellings_in_housing_companies_price_index=old_dwellings_in_housing_companies_price_index,
    )
    index_point_figure_yearly_factory(
        value=101, year=2021, index=old_dwellings_in_housing_companies_price_index
    )
    index_point_figure_yearly_factory(
        value=102, year=2022, index=old_dwellings_in_housing_companies_price_index
    )
    rent.set_start_price_index_point_figure()

    assert rent.start_price_index_point_figure_year is None
    assert rent.start_price_index_point_figure_value is None


@pytest.mark.django_db
def test_set_start_price_index_point_figure(
    rent_factory,
    lease_factory,
    old_dwellings_in_housing_companies_price_index_factory,
    index_point_figure_yearly_factory,
):
    """If the rent has a periodic rent adjustment, the price index's point figure
    value and year should be set in the rent.

    The point figure must correspond to the year previous to the LEASE's start date,
    e.g. year 2023's point figure if lease started in 2024."""
    lease = lease_factory(start_date=date(year=2024, month=1, day=1))
    old_dwellings_in_housing_companies_price_index = (
        old_dwellings_in_housing_companies_price_index_factory()
    )
    index_point_figure_yearly_factory(
        value=101, year=2021, index=old_dwellings_in_housing_companies_price_index
    )
    index_point_figure_yearly_factory(
        value=102, year=2022, index=old_dwellings_in_housing_companies_price_index
    )
    expected_point_figure = index_point_figure_yearly_factory(
        value=103, year=2023, index=old_dwellings_in_housing_companies_price_index
    )
    index_point_figure_yearly_factory(
        value=104, year=2024, index=old_dwellings_in_housing_companies_price_index
    )
    rent: Rent = rent_factory(
        lease=lease,
        old_dwellings_in_housing_companies_price_index=old_dwellings_in_housing_companies_price_index,
    )
    rent.set_start_price_index_point_figure()

    assert rent.start_price_index_point_figure_value == expected_point_figure.value
    assert rent.start_price_index_point_figure_year == expected_point_figure.year
