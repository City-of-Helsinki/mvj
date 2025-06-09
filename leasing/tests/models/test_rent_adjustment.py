from datetime import date
from decimal import Decimal

import pytest

from leasing.calculation.result import CalculationAmount
from leasing.enums import (
    DueDatesType,
    PeriodType,
    RentAdjustmentAmountType,
    RentAdjustmentType,
    RentCycle,
    RentType,
)
from leasing.models.rent import ContractRent, Rent, RentAdjustment, RentIntendedUse


@pytest.mark.django_db
def test_rent_adjustment_get_amount_for_date_range(
    index_factory,
    lease_test_data,
    rent_factory,
    contract_rent_factory,
    rent_adjustment_factory,
):
    lease = lease_test_data["lease"]

    rent = rent_factory(
        lease=lease,
        type=RentType.INDEX2022,
        cycle=RentCycle.JANUARY_TO_DECEMBER,
        due_dates_type=DueDatesType.FIXED,
        due_dates_per_year=1,
    )
    index = index_factory(year=2020, month=1, number=1)

    contract_rent: ContractRent = contract_rent_factory(
        rent=rent,
        intended_use_id=1,
        amount=Decimal(250_000),
        period=PeriodType.PER_YEAR,
        base_amount=Decimal(250_000),
        base_amount_period=PeriodType.PER_YEAR,
        index=index,
    )
    contact_rent_amount = contract_rent.get_amount_for_date_range(
        date(year=2020, month=1, day=1), date(year=2020, month=12, day=31)
    )
    rent_adjustment_shared_values = {
        "rent": rent,
        "intended_use": contract_rent.intended_use,
        "type": RentAdjustmentType.DISCOUNT,
        "start_date": date(year=2020, month=1, day=1),
        "end_date": date(year=2025, month=12, day=31),
    }
    rent_adjustment_1: RentAdjustment = rent_adjustment_factory(
        **rent_adjustment_shared_values,
        amount_type=RentAdjustmentAmountType.PERCENT_PER_YEAR,
        full_amount=Decimal(10),
    )
    rent_adjustment_2: RentAdjustment = rent_adjustment_factory(
        **rent_adjustment_shared_values,
        amount_type=RentAdjustmentAmountType.AMOUNT_TOTAL,
        full_amount=Decimal(100_000),
    )
    rent_adjustment_3: RentAdjustment = rent_adjustment_factory(
        **rent_adjustment_shared_values,
        amount_type=RentAdjustmentAmountType.AMOUNT_TOTAL,
        full_amount=Decimal(250_000),
    )
    rent_adjustment_4: RentAdjustment = rent_adjustment_factory(
        **rent_adjustment_shared_values,
        amount_type=RentAdjustmentAmountType.AMOUNT_PER_YEAR,
        full_amount=Decimal(50_000),
    )
    adjustments = [
        (rent_adjustment_1, Decimal(-25_000)),
        (rent_adjustment_2, Decimal(-100_000)),
        (rent_adjustment_3, Decimal(-250_000)),
        (rent_adjustment_4, Decimal(-50_000)),
    ]
    amount = contact_rent_amount.amount
    date_range_start = date(year=2020, month=1, day=1)
    date_range_end = date(year=2020, month=12, day=31)
    adjustment_amounts = Decimal(0)
    for rent_adjustment, expected_amount in adjustments:
        adjustment_amount_for_range = rent_adjustment.get_amount_for_date_range(
            amount, date_range_start, date_range_end
        )
        assert adjustment_amount_for_range.amount == expected_amount
        adjustment_amounts += adjustment_amount_for_range.amount


@pytest.mark.django_db
@pytest.mark.parametrize(
    "rent_amount_left, adjustment_full_amount, expected_amount_left",
    [
        (100_000, 100_000, 0),
        (50_000, 100_000, 50_000),
        (100_000, 50_000, 0),
        (0, 0, 0),
        (10, Decimal(10.5), Decimal(0.5).quantize(Decimal("0.00"))),
        (Decimal(0.99), 1, Decimal(0.01).quantize(Decimal("0.00"))),
    ],
)
def test_rent_adjustment_update_total_adjustment_amount_left(
    lease_factory,
    rent_factory,
    rent_intended_use_factory,
    rent_adjustment_factory,
    rent_amount_left,
    adjustment_full_amount,
    expected_amount_left,
):
    rent_amount_left = Decimal(rent_amount_left)
    adjustment_full_amount = Decimal(adjustment_full_amount)
    expected_amount_left = Decimal(expected_amount_left)

    rent_adjustment: RentAdjustment = rent_adjustment_factory(
        rent=rent_factory(lease=lease_factory()),
        intended_use=rent_intended_use_factory(),
        amount_type=RentAdjustmentAmountType.AMOUNT_TOTAL,
        full_amount=adjustment_full_amount,
    )
    date_range_start = date(year=2025, month=1, day=1)
    date_range_end = date(year=2025, month=12, day=31)
    calculation = CalculationAmount(
        item=rent_adjustment,
        amount=rent_amount_left,
        date_range_start=date_range_start,
        date_range_end=date_range_end,
    )
    RentAdjustment.update_total_adjustment_amount_left(calculation)
    rent_adjustment.refresh_from_db()
    assert rent_adjustment.amount_left == expected_amount_left


@pytest.mark.django_db
@pytest.mark.parametrize(
    "rent_adjustments_kwargs, inputs",
    [
        pytest.param(  # Case 1: One AMOUNT TOTAL discount
            [
                {
                    "adjustment_type": RentAdjustmentType.DISCOUNT,
                    "amount_type": RentAdjustmentAmountType.AMOUNT_TOTAL,
                    "full_amount": 50_000,
                }
            ],
            {
                "rent_amount": Decimal(100_000),
                "expected_adjustment_total": Decimal(-50_000),
                "expected_discount_amount_left": Decimal(0),
            },
            id="Case 1",
        ),
        pytest.param(  # Case 2 vol 1: AMOUNT_TOTAL first
            [
                {
                    "adjustment_type": RentAdjustmentType.DISCOUNT,
                    "amount_type": RentAdjustmentAmountType.AMOUNT_TOTAL,
                    "full_amount": 50_000,
                },
                {
                    "adjustment_type": RentAdjustmentType.DISCOUNT,
                    "amount_type": RentAdjustmentAmountType.PERCENT_PER_YEAR,
                    "full_amount": 10,
                },
            ],
            {
                "rent_amount": Decimal(100_000),
                "expected_adjustment_total": Decimal(-60_000),
                "expected_discount_amount_left": Decimal(0),
            },
            id="Case 2.1",
        ),
        pytest.param(  # Case 2 vol 2: PERCENT_PER_YEAR first, proves order does not matter
            [
                {
                    "adjustment_type": RentAdjustmentType.DISCOUNT,
                    "amount_type": RentAdjustmentAmountType.PERCENT_PER_YEAR,
                    "full_amount": 10,
                },
                {
                    "adjustment_type": RentAdjustmentType.DISCOUNT,
                    "amount_type": RentAdjustmentAmountType.AMOUNT_TOTAL,
                    "full_amount": 50_000,
                },
            ],
            {
                "rent_amount": Decimal(100_000),
                "expected_adjustment_total": Decimal(-60_000),
                "expected_discount_amount_left": Decimal(0),
            },
            id="Case 2.2",
        ),
        pytest.param(  # Case 3.1: There should be some AMOUNT_TOTAL adjustment left
            [
                {
                    "adjustment_type": RentAdjustmentType.DISCOUNT,
                    "amount_type": RentAdjustmentAmountType.PERCENT_PER_YEAR,
                    "full_amount": 10,
                },
                {
                    "adjustment_type": RentAdjustmentType.DISCOUNT,
                    "amount_type": RentAdjustmentAmountType.AMOUNT_TOTAL,
                    "full_amount": 100_000,
                },
            ],
            {
                "rent_amount": Decimal(100_000),
                "expected_adjustment_total": Decimal(-100_000),
                "expected_discount_amount_left": Decimal(10_000),
            },
            id="Case 3.1",
        ),
        pytest.param(
            # Case 3.2: There should be some AMOUNT_TOTAL adjustment left
            # Ensure that PERCENT_PER_YEAR is applied first, even though it comes last in parameters.
            [
                {
                    "adjustment_type": RentAdjustmentType.DISCOUNT,
                    "amount_type": RentAdjustmentAmountType.AMOUNT_TOTAL,
                    "full_amount": 100_000,
                },
                {
                    "adjustment_type": RentAdjustmentType.DISCOUNT,
                    "amount_type": RentAdjustmentAmountType.PERCENT_PER_YEAR,
                    "full_amount": 10,
                },
            ],
            {
                "rent_amount": Decimal(100_000),
                "expected_adjustment_total": Decimal(-100_000),
                "expected_discount_amount_left": Decimal(10_000),
            },
            id="Case 3.2",
        ),
        pytest.param(
            # Case 4 vol1: Percentage discounts are applied one by one,
            # so **two 50% discounts lead to 75% discount (not 100%)!**
            # This is how it is, and nobody knows why.
            [
                {
                    "adjustment_type": RentAdjustmentType.DISCOUNT,
                    "amount_type": RentAdjustmentAmountType.PERCENT_PER_YEAR,
                    "full_amount": 50,  # 50%
                },
                {
                    "adjustment_type": RentAdjustmentType.DISCOUNT,
                    "amount_type": RentAdjustmentAmountType.PERCENT_PER_YEAR,
                    "full_amount": 50,  # 50%
                },
            ],
            {
                "rent_amount": Decimal(100_000),
                "expected_adjustment_total": Decimal(-75_000),
                "expected_discount_amount_left": None,  # Not used as this test does not have AMOUNT_TOTAL adjustment
            },
            id="Case 4.1",
        ),
        pytest.param(
            # Case 4 vol2: Percentage discounts are applied one by one,
            # and **two 50% discounts lead to a 75% discount (not 100%)!**
            # Ensures that PERCENT_PER_YEAR is applied first before AMOUNT_TOTAL.
            [
                {
                    "adjustment_type": RentAdjustmentType.DISCOUNT,
                    "amount_type": RentAdjustmentAmountType.PERCENT_PER_YEAR,
                    "full_amount": 50,  # 50%
                },
                {
                    "adjustment_type": RentAdjustmentType.DISCOUNT,
                    "amount_type": RentAdjustmentAmountType.AMOUNT_TOTAL,
                    "full_amount": 100_000,
                },
                {
                    "adjustment_type": RentAdjustmentType.DISCOUNT,
                    "amount_type": RentAdjustmentAmountType.PERCENT_PER_YEAR,
                    "full_amount": 50,  # 50%
                },
            ],
            {
                "rent_amount": Decimal(100_000),
                "expected_adjustment_total": Decimal(-100_000),
                "expected_discount_amount_left": Decimal(75_000),
            },
            id="Case 4.2",
        ),
        pytest.param(  # Case 5 vol1: Use amount per year first, AMOUNT_TOTAL adjustment left should not be used at all
            [
                {
                    "adjustment_type": RentAdjustmentType.DISCOUNT,
                    "amount_type": RentAdjustmentAmountType.AMOUNT_PER_YEAR,
                    "full_amount": 50_000,
                },
                {
                    "adjustment_type": RentAdjustmentType.DISCOUNT,
                    "amount_type": RentAdjustmentAmountType.AMOUNT_TOTAL,
                    "full_amount": 100_000,
                },
                {
                    "adjustment_type": RentAdjustmentType.DISCOUNT,
                    "amount_type": RentAdjustmentAmountType.PERCENT_PER_YEAR,
                    "full_amount": 50,  # 50%
                },
            ],
            {
                "rent_amount": Decimal(100_000),
                "expected_adjustment_total": Decimal(-100_000),
                "expected_discount_amount_left": Decimal(100_000),
            },
            id="Case 5.1",
        ),
        pytest.param(
            # Case 5 vol2: Use percent first, AMOUNT_TOTAL adjustment left should not be used at all
            # Same as above (5.1) but with different order.
            [
                {
                    "adjustment_type": RentAdjustmentType.DISCOUNT,
                    "amount_type": RentAdjustmentAmountType.PERCENT_PER_YEAR,
                    "full_amount": 50,  # 50%
                },
                {
                    "adjustment_type": RentAdjustmentType.DISCOUNT,
                    "amount_type": RentAdjustmentAmountType.AMOUNT_PER_YEAR,
                    "full_amount": 50_000,
                },
                {
                    "adjustment_type": RentAdjustmentType.DISCOUNT,
                    "amount_type": RentAdjustmentAmountType.AMOUNT_TOTAL,
                    "full_amount": 100_000,
                },
            ],
            {
                "rent_amount": Decimal(100_000),
                "expected_adjustment_total": Decimal(-100_000),
                "expected_discount_amount_left": Decimal(100_000),
            },
            id="Case 5.2",
        ),
        pytest.param(
            # Case 6 vol1: Add increases, AMOUNT_TOTAL adjustment should be fully used
            # DISCOUNT AND INCREASE cancel each other out.
            [
                {
                    "adjustment_type": RentAdjustmentType.DISCOUNT,
                    "amount_type": RentAdjustmentAmountType.PERCENT_PER_YEAR,
                    "full_amount": 50,  # 50%
                },
                {
                    "adjustment_type": RentAdjustmentType.DISCOUNT,
                    "amount_type": RentAdjustmentAmountType.AMOUNT_PER_YEAR,
                    "full_amount": 50_000,
                },
                {
                    "adjustment_type": RentAdjustmentType.DISCOUNT,
                    "amount_type": RentAdjustmentAmountType.AMOUNT_TOTAL,
                    "full_amount": 100_000,
                },
                {
                    "adjustment_type": RentAdjustmentType.INCREASE,
                    "amount_type": RentAdjustmentAmountType.AMOUNT_PER_YEAR,
                    "full_amount": 100_000,
                },
            ],
            {
                "rent_amount": Decimal(100_000),
                "expected_adjustment_total": Decimal(-100_000),
                "expected_discount_amount_left": Decimal(0),
            },
            id="Case 6.1",
        ),
        pytest.param(
            # Case 6 vol2: Add increases, AMOUNT_TOTAL adjustment should be half used.
            # Note: RentAdjustment.get_sort_priority(), AMOUNT_TOTAL adjustments are processed last.
            [
                {
                    "adjustment_type": RentAdjustmentType.DISCOUNT,
                    "amount_type": RentAdjustmentAmountType.PERCENT_PER_YEAR,
                    "full_amount": 25,  # 25%
                },
                {
                    "adjustment_type": RentAdjustmentType.DISCOUNT,
                    "amount_type": RentAdjustmentAmountType.AMOUNT_TOTAL,
                    "full_amount": 100_000,
                },
                {
                    "adjustment_type": RentAdjustmentType.INCREASE,
                    "amount_type": RentAdjustmentAmountType.AMOUNT_PER_YEAR,
                    "full_amount": 25_000,
                },
            ],
            {
                "rent_amount": Decimal(100_000),
                "expected_adjustment_total": Decimal(-100_000),
                "expected_discount_amount_left": Decimal(0),
            },
            id="Case 6.2",
        ),
        pytest.param(  # Case 7: Increases don't add to AMOUNT_TOTAL discount adjustments amount_left
            [
                {
                    "adjustment_type": RentAdjustmentType.DISCOUNT,
                    "amount_type": RentAdjustmentAmountType.AMOUNT_TOTAL,
                    "full_amount": 50_000,
                },
                {
                    "adjustment_type": RentAdjustmentType.INCREASE,
                    "amount_type": RentAdjustmentAmountType.AMOUNT_PER_YEAR,
                    "full_amount": 100_000,
                },
            ],
            {
                "rent_amount": Decimal(100_000),
                "expected_adjustment_total": Decimal(50_000),
                "expected_discount_amount_left": Decimal(0),
            },
            id="Case 7",
        ),
        pytest.param(  # Case 8: Increases neutralize discounts on AMOUNT_TOTAL adjustments amount_left
            [
                {
                    "adjustment_type": RentAdjustmentType.DISCOUNT,
                    "amount_type": RentAdjustmentAmountType.AMOUNT_TOTAL,
                    "full_amount": 50_000,
                },
                {
                    "adjustment_type": RentAdjustmentType.INCREASE,
                    "amount_type": RentAdjustmentAmountType.AMOUNT_PER_YEAR,
                    "full_amount": 50_000,
                },
            ],
            {
                "rent_amount": Decimal(100_000),
                "expected_adjustment_total": Decimal(0),
                "expected_discount_amount_left": Decimal(0),
            },
            id="Case 8",
        ),
        pytest.param(
            # Case 9: Increases don't add to AMOUNT_TOTAL discount adjustments amount_left when rent is fully discounted
            # but discount should be then applied from the increase
            [
                {
                    "adjustment_type": RentAdjustmentType.DISCOUNT,
                    "amount_type": RentAdjustmentAmountType.AMOUNT_TOTAL,
                    "full_amount": 50_000,
                },
                {
                    "adjustment_type": RentAdjustmentType.INCREASE,
                    "amount_type": RentAdjustmentAmountType.AMOUNT_TOTAL,
                    "full_amount": 100_000,
                },
            ],
            {
                "rent_amount": Decimal(0),
                "expected_adjustment_total": Decimal(
                    50_000
                ),  # INCREASE +50_000, not discount
                "expected_discount_amount_left": Decimal(0),
            },
            id="Case 9",
        ),
    ],
)
def test_rent_adjustment_calculate_and_process_rent_adjustments(
    lease_factory,
    rent_factory,
    fixed_initial_year_rent_factory,
    rent_intended_use_factory,
    rent_adjustment_factory,
    rent_adjustments_kwargs,
    inputs,
):
    """
    Tests that the combined total of rent adjustments are calculated correctly,
    and that for a single discount of type AMOUNT_TOTAL the amount_left is updated as expected after processing.
    """
    rent_amount = inputs.get("rent_amount")
    expected_adjustment_total = inputs.get("expected_adjustment_total")
    expected_discount_amount_left = inputs.get("expected_discount_amount_left")
    start_date = date(year=2025, month=1, day=1)
    end_date = date(year=2025, month=12, day=31)
    rent: Rent = rent_factory(
        lease=lease_factory(start_date=start_date, end_date=end_date),
        type=RentType.FIXED,
        start_date=start_date,
        end_date=end_date,
    )
    rent_intended_use: RentIntendedUse = rent_intended_use_factory()
    fixed_initial_year_rent_factory(
        rent=rent,
        amount=rent_amount,
        intended_use=rent_intended_use,
        start_date=start_date,
        end_date=end_date,
    )
    for rent_adjustment_kwarg in rent_adjustments_kwargs:
        adjustment_type = rent_adjustment_kwarg.get("adjustment_type")
        amount_type = rent_adjustment_kwarg.get("amount_type")
        adjustment_full_amount = rent_adjustment_kwarg.get("full_amount")
        rent_adjustment_factory(
            rent=rent,
            intended_use=rent_intended_use,
            type=adjustment_type,
            amount_type=amount_type,
            full_amount=adjustment_full_amount,
        )

    period = (start_date, end_date)

    calculation_amounts = rent.calculate_and_process_rent_adjustments(
        rent_intended_use, rent_amount, period, dry_run=False
    )
    assert sum([x.amount for x in calculation_amounts]) == expected_adjustment_total
    for calculation_amount in calculation_amounts:
        if (
            not calculation_amount.item.amount_type
            == RentAdjustmentAmountType.AMOUNT_TOTAL
        ):
            continue
        if calculation_amount.item.type == RentAdjustmentType.DISCOUNT:
            calculation_amount.item.refresh_from_db()
            assert calculation_amount.item.amount_left == expected_discount_amount_left
        elif calculation_amount.item.type == RentAdjustmentType.INCREASE:
            calculation_amount.item.refresh_from_db()
            assert calculation_amount.item.amount_left == Decimal(
                0
            )  # Should always be used in one go
