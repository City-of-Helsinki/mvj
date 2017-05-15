from datetime import date

import pytest

from leasing.enums import LeaseState

billing_periods_for_year_data = (
    (2017, 1, [
        (date(2017, 1, 1), date(2017, 12, 31))
    ]),
    (2017, 2, [
        (date(2017, 1, 1), date(2017, 6, 30)),
        (date(2017, 7, 1), date(2017, 12, 31)),
    ]),
    (2017, 3, [
        (date(2017, 1, 1), date(2017, 4, 30)),
        (date(2017, 5, 1), date(2017, 8, 31)),
        (date(2017, 9, 1), date(2017, 12, 31)),
    ]),
    (2017, 4, [
        (date(2017, 1, 1), date(2017, 3, 31)),
        (date(2017, 4, 1), date(2017, 6, 30)),
        (date(2017, 7, 1), date(2017, 9, 30)),
        (date(2017, 10, 1), date(2017, 12, 31)),
    ]),
    (2017, 6, [
        (date(2017, 1, 1), date(2017, 2, 28)),
        (date(2017, 3, 1), date(2017, 4, 30)),
        (date(2017, 5, 1), date(2017, 6, 30)),
        (date(2017, 7, 1), date(2017, 8, 31)),
        (date(2017, 9, 1), date(2017, 10, 31)),
        (date(2017, 11, 1), date(2017, 12, 31)),
    ]),
)


@pytest.mark.django_db
@pytest.mark.parametrize('year, bills_per_year, expected', billing_periods_for_year_data)
def test_get_billing_periods_for_year(lease_factory, year, bills_per_year, expected):
    lease = lease_factory(
        state=LeaseState.DRAFT,
        is_billing_enabled=True,
        bills_per_year=bills_per_year,
    )

    assert lease.get_billing_periods_for_year(year) == expected


current_billing_period_for_date_data = (
    (date(2017, 5, 5), 1, (date(2017, 1, 1), date(2017, 12, 31))),
    (date(2017, 5, 5), 2, (date(2017, 1, 1), date(2017, 6, 30))),
)


@pytest.mark.django_db
@pytest.mark.parametrize('date, bills_per_year, expected', current_billing_period_for_date_data)
def test_get_current_billing_period_for_date(lease_factory, date, bills_per_year, expected):
    lease = lease_factory(
        state=LeaseState.DRAFT,
        is_billing_enabled=True,
        bills_per_year=bills_per_year,
    )

    assert lease.get_current_billing_period_for_date(date) == expected


next_billing_period_for_date_data = (
    (date(2017, 5, 5), 1, (date(2018, 1, 1), date(2018, 12, 31))),
    (date(2017, 5, 5), 2, (date(2017, 7, 1), date(2017, 12, 31))),
)


@pytest.mark.django_db
@pytest.mark.parametrize('date, bills_per_year, expected', next_billing_period_for_date_data)
def test_get_next_billing_period_for_date(lease_factory, date, bills_per_year, expected):
    lease = lease_factory(
        state=LeaseState.DRAFT,
        is_billing_enabled=True,
        bills_per_year=bills_per_year,
    )

    assert lease.get_next_billing_period_for_date(date) == expected
