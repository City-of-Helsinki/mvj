# TODO
# - 20 vuoden kuluttajahintaindeksien tarkistukset
# - harkinnanvaraisuus
#   - esim "tähän vuokraukseen sovelletaan vain 50% täydestä määrästä"
#   - esim "ei sovelleta lainkaan tällä kertaa"
# - mitä muuta voisi vaikuttaa?


from collections.abc import Callable

import pytest

from leasing.models.lease import Lease
from leasing.models.rent import (
    IndexPointFigureYearly,
    OldDwellingsInHousingCompaniesPriceIndex,
    Rent,
)


@pytest.fixture(scope="module")
def example_data(
    rent_factory: Callable[..., Rent],
    lease_with_generated_service_unit_factory: Callable[..., Lease],
    old_dwellings_in_housing_companies_price_index_factory: Callable[
        ..., OldDwellingsInHousingCompaniesPriceIndex
    ],
    index_point_figure_factory: Callable[..., IndexPointFigureYearly],
):
    """
    Initializes example data for the calculation example.

    This function should be run once to set up the necessary data.
    """
    # Create index
    index = old_dwellings_in_housing_companies_price_index_factory(
        code="test_index_for_2045",
        name="Price index of old dwellings in housing companies (2020=100)",
    )

    # Create index point figures
    point_figure_years_and_values = [
        (2020, 100.0),  # Base year index
        (2025, 90.0),  # Year of rent start
        (2040, 150.0),  # Unused
        (2041, 160.0),  # Unused
        (2042, 170.0),  # N-3
        (2043, 180.0),  # N-2, value is twice of rent start's index point figure value
        (2044, 190.0),  # N-1
        (2045, 200.0),  # year of calculation (N)
    ]
    point_figures = [
        index_point_figure_factory(index=index, year=year, figure=value)
        for year, value in point_figure_years_and_values
    ]

    rent = rent_factory()  # TODO necessary parameters

    # TODO initializeFixedInitialYearRent, because the calculation.py uses that
    fixed_initial_year_rent = None

    # Return to the data for easy access in the example
    return {
        "rent": rent,
        "fixed_initial_year_rent": fixed_initial_year_rent,
        "index": index,
        "point_figures": point_figures,
    }


@pytest.mark.django_db
def test_apply_periodic_rent_adjustment_example(example_data):
    rent = example_data["rent"]
    fixed_initial_year_rent = example_data["fixed_initial_year_rent"]
    index = example_data["index"]
    point_figures = example_data["point_figures"]

    # TODO write down expected calculation results
    # TODO apply the calculation function
    # TODO asserts
    # TODO any last words?

    pass
