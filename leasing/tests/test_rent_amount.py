from datetime import date

import pytest

from leasing.enums import LeaseState, RentType

get_amount_for_period_data = (
    (date(2017, 5, 1), date(2018, 1, 1), RentType.FREE, 0.0),
    (date(2017, 5, 1), date(2017, 7, 1), RentType.MANUAL, 0.0),
    (date(2017, 5, 1), date(2017, 7, 1), RentType.ONE_TIME, 500.0),
    (date(2017, 1, 1), date(2017, 12, 31), RentType.FIXED, 6000.0),
    (date(2017, 7, 1), date(2017, 12, 31), RentType.FIXED, 3000.0),
)


@pytest.mark.django_db
@pytest.mark.parametrize('period_start_date, period_end_date, rent_type, expected', get_amount_for_period_data)
def test_get_amount_for_period(lease_factory, rent_factory, period_start_date, period_end_date, rent_type, expected):
    lease = lease_factory(state=LeaseState.DRAFT, is_billing_enabled=True, bills_per_year=12)

    rent = rent_factory(
        lease=lease,
        type=rent_type,
        amount=500,
    )

    assert rent.get_amount_for_period(period_start_date, period_end_date) == expected
