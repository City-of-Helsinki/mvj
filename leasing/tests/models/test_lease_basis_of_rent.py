from decimal import Decimal

import pytest

from leasing.enums import AreaUnit, BasisOfRentType, SubventionType


@pytest.mark.django_db
def test_calculate_subvented_initial_year_rent_form_of_management(
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
        index=index,
        type=BasisOfRentType.LEASE,
        area=Decimal(2803.00),
        area_unit=AreaUnit.FLOOR_SQUARE_METRE,
        amount_per_area=Decimal(37.00),
        profit_margin_percentage=Decimal(4.00),
        discount_percentage=Decimal(37.000000),
        subvention_type=SubventionType.FORM_OF_MANAGEMENT,
    )

    # If there are no management subventions, the subvented initial year rent
    # should be the same as the initial year rent
    assert round(
        lease_basis_of_rent.calculate_subvented_initial_year_rent(), 2
    ) == round(lease_basis_of_rent.calculate_initial_year_rent(), 2)

    # In the case when there is a management subvention,
    # expect a certain number subvented initial year rent
    # with the accuracy of two decimals
    lease_basis_of_rent_management_subvention_factory(
        lease_basis_of_rent=lease_basis_of_rent,
        subvention_amount=516.45,
        management_id=1,
    )

    expected_subvented_initial_year_rent = Decimal(57903.92)

    assert round(
        lease_basis_of_rent.calculate_subvented_initial_year_rent(), 2
    ) == round(expected_subvented_initial_year_rent, 2)


@pytest.mark.django_db
def test_calculate_subvented_initial_year_rent_re_lease(
    index_factory,
    lease_basis_of_rent_factory,
    lease_factory,
):
    index = index_factory(
        number=2161,
        year=2022,
    )

    # If there are no subventions, the subvented initial year rent
    # should be the same as the initial year rent
    lease_basis_of_rent_without_subvention = lease_basis_of_rent_factory(
        lease=lease_factory(),
        type=BasisOfRentType.LEASE,
        index=index,
        area=Decimal(17987.00),
        area_unit=AreaUnit.FLOOR_SQUARE_METRE,
        amount_per_area=Decimal(49.00),
        profit_margin_percentage=Decimal(5.00),
        discount_percentage=Decimal(27.800000),
    )

    assert round(
        lease_basis_of_rent_without_subvention.calculate_subvented_initial_year_rent(),
        2,
    ) == round(lease_basis_of_rent_without_subvention.calculate_initial_year_rent(), 2)

    # In the case when there is a re-lease subvention,
    # expect a certain number subvented initial year rent
    # with the accuracy of two decimals
    lease_basis_of_rent = lease_basis_of_rent_factory(
        lease=lease_factory(),
        type=BasisOfRentType.LEASE,
        index=index,
        area=Decimal(17987.00),
        area_unit=AreaUnit.FLOOR_SQUARE_METRE,
        amount_per_area=Decimal(49.00),
        profit_margin_percentage=Decimal(5.00),
        discount_percentage=Decimal(27.800000),
        subvention_type=SubventionType.RE_LEASE,
        subvention_base_percent=Decimal(5.00),
        subvention_graduated_percent=Decimal(5.00),
    )

    expected_subvented_initial_year_rent = Decimal(859462.23)

    assert round(
        lease_basis_of_rent.calculate_subvented_initial_year_rent(), 2
    ) == round(expected_subvented_initial_year_rent, 2)
