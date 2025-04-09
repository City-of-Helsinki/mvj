from decimal import Decimal

import pytest

from leasing.enums import AreaUnit, BasisOfRentType, SubventionType


@pytest.mark.django_db
def test_calculate_initial_year_rent(
    index_factory,
    lease_basis_of_rent_factory,
    lease_factory,
):
    index = index_factory(
        number=1951,
        year=2018,
        month=8,
    )
    area = Decimal(12580.00)
    amount_per_area = Decimal(29.00)
    profit_margin_percentage = Decimal(5.00)

    lease_basis_of_rent = lease_basis_of_rent_factory(
        lease=lease_factory(),
        type=BasisOfRentType.LEASE,
        index=index,
        area=Decimal(0.00),
        area_unit=AreaUnit.FLOOR_SQUARE_METRE,
        amount_per_area=Decimal(0.00),
        profit_margin_percentage=Decimal(0.00),
    )

    # In the case when there is no area,
    # initial year rent should be 0
    lease_basis_of_rent.area = Decimal(0.00)
    lease_basis_of_rent.amount_per_area = amount_per_area
    lease_basis_of_rent.profit_margin_percentage = profit_margin_percentage

    assert round(lease_basis_of_rent.calculate_initial_year_rent(), 2) == Decimal(0.00)

    # In the case when there is no amount_per_area,
    # initial year rent should be 0
    lease_basis_of_rent.area = area
    lease_basis_of_rent.amount_per_area = Decimal(0.00)
    lease_basis_of_rent.profit_margin_percentage = profit_margin_percentage

    assert round(lease_basis_of_rent.calculate_initial_year_rent(), 2) == Decimal(0.00)

    # In the case when there is no profit_margin_percentage,
    # initial year rent should be 0
    lease_basis_of_rent.area = area
    lease_basis_of_rent.amount_per_area = amount_per_area
    lease_basis_of_rent.profit_margin_percentage = Decimal(0.00)

    assert round(lease_basis_of_rent.calculate_initial_year_rent(), 2) == Decimal(0.00)

    # In the case when
    # area, amount_per_area and profit_margin_percentage
    # are all defined and greater than 0,
    # expect a certain number for initial year rent with the accuracy of two decimals
    lease_basis_of_rent.area = area
    lease_basis_of_rent.amount_per_area = amount_per_area
    lease_basis_of_rent.profit_margin_percentage = profit_margin_percentage

    expected_initial_year_rent = Decimal(355881.91)

    assert round(lease_basis_of_rent.calculate_initial_year_rent(), 2) == round(
        expected_initial_year_rent, 2
    )


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


@pytest.mark.django_db
def test_calculate_temporary_subvention_data(
    lease_basis_of_rent_factory,
    lease_basis_of_rent_management_subvention_factory,
    lease_basis_of_rent_temporary_subvention_factory,
    lease_factory,
    index_factory,
):
    lease_basis_of_rent = lease_basis_of_rent_factory(
        lease=lease_factory(),
        type=BasisOfRentType.LEASE,
        index=index_factory(number=1976, year=2020, month=2),
        area=Decimal(2969.00),
        area_unit=AreaUnit.FLOOR_SQUARE_METRE,
        amount_per_area=Decimal(37.00),
        profit_margin_percentage=Decimal(4.00),
        discount_percentage=Decimal(28.000000),
    )

    lease_basis_of_rent_management_subvention_factory(
        lease_basis_of_rent=lease_basis_of_rent,
        subvention_amount=731.12,
    )
    # In the case when there are no temporary subventions,
    # a dictionary with an empty list and the total amount of subventions as 0
    # should be returned
    assert lease_basis_of_rent.calculate_temporary_subvention_data() == {
        "temporary_subventions": [],
        "total_amount_euros_per_year": Decimal(0),
    }

    # In the case when there are temporary subventions,
    # expect a certain number for the sum of cumulative temporary subventions
    # with the accuracy of two decimals
    lease_basis_of_rent_temporary_subvention_factory(
        lease_basis_of_rent=lease_basis_of_rent,
        description="Temporary subvention 1",
        subvention_percent=10.00,
    )

    lease_basis_of_rent_temporary_subvention_factory(
        lease_basis_of_rent=lease_basis_of_rent,
        description="Temporary subvention 2",
        subvention_percent=20.00,
    )

    expected_temporary_subvention_data = {
        "temporary_subventions": [
            {
                "description": "Temporary subvention 1",
                "subvention_percent": 10.00,
                "subvention_amount_euros_per_year": Decimal(8682.78100000),
            },
            {
                "description": "Temporary subvention 2",
                "subvention_percent": 20.00,
                "subvention_amount_euros_per_year": Decimal(15629.0058000000),
            },
        ],
        "total_amount_euros_per_year": Decimal(24311.7868000000),
    }

    temporary_subvention_data = (
        lease_basis_of_rent.calculate_temporary_subvention_data()
    )

    assert round(temporary_subvention_data["total_amount_euros_per_year"], 2) == round(
        expected_temporary_subvention_data["total_amount_euros_per_year"], 2
    )

    # Check that the subvention amounts match the expected subvention amounts
    # with the accuracy of three decimals
    subventions = zip(
        temporary_subvention_data["temporary_subventions"],
        expected_temporary_subvention_data["temporary_subventions"],
    )

    for subvention, expected_subvention in subventions:
        assert round(subvention["subvention_amount_euros_per_year"], 3) == round(
            expected_subvention["subvention_amount_euros_per_year"], 3
        )


@pytest.mark.django_db
def test_calculate_temporary_subvention_percentage(
    lease_basis_of_rent_factory,
    lease_factory,
    index_factory,
    lease_basis_of_rent_temporary_subvention_factory,
):
    lease_basis_of_rent = lease_basis_of_rent_factory(
        lease=lease_factory(),
        type=BasisOfRentType.LEASE,
        index=index_factory(number=1976, year=2020, month=2),
        area=Decimal(2969.00),
        area_unit=AreaUnit.FLOOR_SQUARE_METRE,
        amount_per_area=Decimal(37.00),
        profit_margin_percentage=Decimal(4.00),
        discount_percentage=Decimal(28.000000),
    )

    # In the case when there are no temporary subventions,
    # the temporary subvention percent should be 0
    assert lease_basis_of_rent.calculate_temporary_subvention_percentage() == Decimal(0)

    # In the case when there are temporary subventions,
    # expect a certain number for the temporary subvention percent
    # with the accuracy of two decimals
    lease_basis_of_rent_temporary_subvention_factory(
        lease_basis_of_rent=lease_basis_of_rent,
        description="Temporary subvention 1",
        subvention_percent=10.00,
    )
    lease_basis_of_rent_temporary_subvention_factory(
        lease_basis_of_rent=lease_basis_of_rent,
        description="Temporary subvention 2",
        subvention_percent=20.00,
    )

    expected_temporary_subvention_percent = Decimal(28.00)

    assert round(
        lease_basis_of_rent.calculate_temporary_subvention_percentage(), 2
    ) == round(expected_temporary_subvention_percent, 2)


@pytest.mark.django_db
def test_calculate_subvention_amount_per_area(
    lease_basis_of_rent_factory,
    lease_basis_of_rent_management_subvention_factory,
    lease_factory,
    index_factory,
):
    # Subvention type: FORM_OF_MANAGEMENT
    # In the case of FORM_OF_MANAGEMENT subvention type,
    # the subvention amount per area equals to
    # the sum of the subvention amounts of management subventions

    lease_basis_of_rent = lease_basis_of_rent_factory(
        lease=lease_factory(),
        type=BasisOfRentType.LEASE,
        index=index_factory(number=2238, year=2022, month=10),
        area=Decimal(107.00),
        area_unit=AreaUnit.FLOOR_SQUARE_METRE,
        amount_per_area=Decimal(500.00),
        profit_margin_percentage=Decimal(5.00),
        discount_percentage=Decimal(35.200000),
        subvention_type=SubventionType.FORM_OF_MANAGEMENT,
    )

    lease_basis_of_rent_management_subvention_factory(
        lease_basis_of_rent=lease_basis_of_rent,
        subvention_amount=500.00,
    )

    lease_basis_of_rent_management_subvention_factory(
        lease_basis_of_rent=lease_basis_of_rent,
        subvention_amount=1000.00,
    )

    expected_subvention_amount_per_area = Decimal(1500.00)

    assert round(
        lease_basis_of_rent.calculate_subvention_amount_per_area(), 2
    ) == round(expected_subvention_amount_per_area, 2)

    # Subvention type: RE_LEASE
    # In the case of RE_LEASE subvention type,
    # the subvention amount per area is derived from the
    # subvention base percent and the subvention graduated percent
    lease_basis_of_rent = lease_basis_of_rent_factory(
        lease=lease_factory(),
        type=BasisOfRentType.LEASE2022,
        index=index_factory(number=2238, year=2022, month=11),
        area=Decimal(107.00),
        area_unit=AreaUnit.FLOOR_SQUARE_METRE,
        amount_per_area=Decimal(500.00),
        profit_margin_percentage=Decimal(5.00),
        discount_percentage=Decimal(35.200000),
        subvention_type=SubventionType.RE_LEASE,
        subvention_base_percent=Decimal(10.00),
        subvention_graduated_percent=Decimal(10.00),
    )

    expected_subvention_amount_per_area = Decimal(405.00)

    assert round(
        lease_basis_of_rent.calculate_subvention_amount_per_area(), 2
    ) == round(expected_subvention_amount_per_area, 2)
