from typing import Callable

import pytest
from _pytest.capture import CaptureFixture
from django.core.management import call_command

from leasing.models.rent import IndexPointFigureYearly, Rent


@pytest.mark.django_db
def test_no_rents_to_update(capfd: CaptureFixture[str]) -> None:
    """
    No Rent objects need updating.
    """
    call_command("update_missing_periodic_rent_adjustment_index_values")
    captured = capfd.readouterr()
    assert (
        "No Rent objects with missing tasotarkistus values to update." in captured.out
    )


@pytest.mark.django_db
def test_update_rent_with_existing_index_point_figure(
    index_point_figure_yearly_factory: Callable[..., IndexPointFigureYearly],
    lease_factory: Callable[..., Rent],
    old_dwellings_in_housing_companies_price_index_factory: Callable[..., str],
    rent_factory: Callable[..., Rent],
) -> None:
    """
    Single rent object is successfully updated.
    """
    price_index = old_dwellings_in_housing_companies_price_index_factory()
    lease = lease_factory(start_date="2025-01-01")
    rent = rent_factory(
        old_dwellings_in_housing_companies_price_index=price_index,
        start_price_index_point_figure_value=None,
        start_price_index_point_figure_year=None,
        lease=lease,
    )
    index_point_figure_yearly_factory(index=price_index, year=2024, value=104)

    call_command("update_missing_periodic_rent_adjustment_index_values")
    rent.refresh_from_db()

    assert rent.start_price_index_point_figure_value == 104
    assert rent.start_price_index_point_figure_year == 2024


@pytest.mark.django_db
def test_missing_index_point_figure(
    lease_factory: Callable[..., Rent],
    old_dwellings_in_housing_companies_price_index_factory: Callable[..., str],
    rent_factory: Callable[..., Rent],
) -> None:
    """
    IndexPointFigureYearly does not exist for the required year so the rent's
    values are not updated.
    """
    price_index = old_dwellings_in_housing_companies_price_index_factory()
    lease = lease_factory(start_date="2025-01-01")
    rent = rent_factory(
        old_dwellings_in_housing_companies_price_index=price_index,
        start_price_index_point_figure_value=None,
        start_price_index_point_figure_year=None,
        lease=lease,
    )

    call_command("update_missing_periodic_rent_adjustment_index_values")
    rent.refresh_from_db()

    assert rent.start_price_index_point_figure_value is None
    assert rent.start_price_index_point_figure_year is None


@pytest.mark.django_db
def test_multiple_rents_updated(
    index_point_figure_yearly_factory: Callable[..., IndexPointFigureYearly],
    lease_factory: Callable[..., Rent],
    old_dwellings_in_housing_companies_price_index_factory: Callable[..., str],
    rent_factory: Callable[..., Rent],
) -> None:
    """
    Multiple Rent objects are updated.
    """
    price_index = old_dwellings_in_housing_companies_price_index_factory()
    lease1 = lease_factory(start_date="2024-01-01")
    lease2 = lease_factory(start_date="2025-01-01")
    rent1 = rent_factory(
        old_dwellings_in_housing_companies_price_index=price_index,
        start_price_index_point_figure_value=None,
        start_price_index_point_figure_year=None,
        lease=lease1,
    )
    rent2 = rent_factory(
        old_dwellings_in_housing_companies_price_index=price_index,
        start_price_index_point_figure_value=None,
        start_price_index_point_figure_year=None,
        lease=lease2,
    )
    index_point_figure_yearly_factory(index=price_index, year=2023, value=103)
    index_point_figure_yearly_factory(index=price_index, year=2024, value=104)

    call_command("update_missing_periodic_rent_adjustment_index_values")
    rent1.refresh_from_db()
    rent2.refresh_from_db()

    assert rent1.start_price_index_point_figure_value == 103
    assert rent1.start_price_index_point_figure_year == 2023

    assert rent2.start_price_index_point_figure_value == 104
    assert rent2.start_price_index_point_figure_year == 2024
