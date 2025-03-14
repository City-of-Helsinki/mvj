from decimal import Decimal

import pytest


@pytest.mark.django_db
def test_calculate_subvented_initial_year_rent(
    index_factory,
    lease_basis_of_rent_factory,
    lease_basis_of_rent_management_subvention_factory,
    lease_factory,
):
    index = index_factory(
        number=1994,
        year=2021,
        month=2,
    )
    lease_basis_of_rent = lease_basis_of_rent_factory(
        lease=lease_factory(),
        intended_use_id=1,
        index=index,
        area=Decimal(2803.00),
        area_unit="kem2",
        amount_per_area=Decimal(37.00),
        profit_margin_percentage=Decimal(4.00),
        discount_percentage=Decimal(37.000000),
        subvention_type="form_of_management",
    )
    lease_basis_of_rent_management_subvention = (  # noqa: F841
        lease_basis_of_rent_management_subvention_factory(
            lease_basis_of_rent=lease_basis_of_rent,
            subvention_amount=516.45,
            management_id=1,
        )
    )

    expected_subvented_initial_year_rent = Decimal(57903.92)

    assert round(
        lease_basis_of_rent.calculate_subvented_initial_year_rent(), 2
    ) == round(expected_subvented_initial_year_rent, 2)
