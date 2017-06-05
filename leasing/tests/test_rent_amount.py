from datetime import date
from decimal import Decimal

import pytest

from leasing.enums import LeaseState, RentType

get_amount_for_period_data = (
    (date(2017, 5, 1), date(2018, 1, 1), RentType.FREE, Decimal(0)),
    (date(2017, 5, 1), date(2017, 7, 1), RentType.MANUAL, Decimal(0)),
    (date(2017, 5, 1), date(2017, 7, 1), RentType.ONE_TIME, Decimal(500)),
    (date(2017, 1, 1), date(2017, 12, 31), RentType.FIXED, Decimal(6000)),
    (date(2017, 7, 1), date(2017, 12, 31), RentType.FIXED, Decimal(3000)),
)


@pytest.mark.django_db
@pytest.mark.parametrize('period_start_date, period_end_date, rent_type, expected', get_amount_for_period_data)
def test_get_amount_for_period(lease_factory, rent_factory, period_start_date, period_end_date, rent_type, expected):
    lease = lease_factory(state=LeaseState.DRAFT, is_billing_enabled=True, bills_per_year=12)

    rent = rent_factory(
        lease=lease,
        type=rent_type,
        amount=Decimal(500),
    )

    result = rent.get_amount_for_period(period_start_date, period_end_date)
    assert result == expected
    assert isinstance(result, Decimal)
