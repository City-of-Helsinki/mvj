"""
This file contains an example calculation for tasotarkistus in 2045.

It is for illustration purposes only and is not used in the actual application.

Please refer to the `./spec` directory for the official specification of tasotarkistus.
"""

import datetime
import logging
import sys
from decimal import Decimal

from dateutil.relativedelta import relativedelta
from django.db.models import Q
from django.utils import timezone

from leasing.enums import PeriodicRentAdjustmentType
from leasing.models.rent import (
    FixedInitialYearRent,
    IndexPointFigureYearly,
    OldDwellingsInHousingCompaniesPriceIndex,
    Rent,
)

logger = logging.getLogger(__name__)
stdout_handler = logging.StreamHandler(stream=sys.stdout)
logger.addHandler(stdout_handler)
logger.setLevel(logging.INFO)


def example(rent: Rent):
    """
    Example function to demonstrate the calculation.
    """
    # NOTE: Filter out rents that
    #   - are not active anymore,
    #   - do not use tasotarkistus,
    # or that match any other disqualifying criteria.

    if not is_correct_year_for_tasotarkistus(rent):
        logger.info("Current year is not a tasotarkistus year for this rent. Skipping.")
        return

    price_index = rent.old_dwellings_in_housing_companies_price_index
    periodic_rent_adjustment_type = rent.periodic_rent_adjustment_type

    if not price_index or not periodic_rent_adjustment_type:
        # One of two things is probably true:
        # 1. Rent does not use tasotarkistus at all, so it can be skipped.
        # 2. Rent should use tasotarkistus, but the index and type are missing.
        #    This might be an error in the rent creation process, or database
        #    state.
        #
        # In either case, we cannot proceed with the calculation.
        logger.info(
            "Rent does not have an associated price index or periodic rent "
            "adjustment type, which are necessary for tasotarkistus calculation. "
            "Skipping."
        )
        return

    tasotarkistus_start_year = get_tasotarkistus_start_year(rent)
    tasotarkistus_point_figure_start_value = get_tasotarkistus_point_figure_start_value(
        rent, tasotarkistus_start_year
    )

    # NOTE: Fetch all applicable objects that contain rent amounts that require
    # adjustment as part tasotarkistus.
    # Below is an example for leasing.models.rent.FixedInitialYearRent:

    old_rent = get_old_rent_amount(rent)

    custom_consideration_percentage = get_custom_consideration_percentage(rent)

    new_rent = calculate_new_rent_amount_after_periodic_rent_adjustment(
        rent_amount=old_rent,
        price_index=price_index,
        adjustment_type=periodic_rent_adjustment_type,
        tasotarkistus_start_year=tasotarkistus_start_year,
        tasotarkistus_point_figure_start_value=tasotarkistus_point_figure_start_value,
        custom_consideration_percentage=custom_consideration_percentage,
        # TODO other parameters?
    )

    logger.info(
        "Calculated new rent after tasotarkistus: %.2f (previous rent: %.2f)",
        new_rent,
        old_rent,
        # TODO anything else to log?
    )

    # NOTE: Then apply the new rent amount to the applicable database objects.

    # NOTE: You might need to save the adjustment details in some intermediate
    # database object that represents the newly adjusted rent with start/end
    # dates, etc.
    # This is necessary to properly calculate the invoices, especially if the
    # adjustment happens mid-invoicing-period.


def is_correct_year_for_tasotarkistus(rent: Rent) -> bool:
    """
    Tasotarkistus is applied for the first time 20 years after the rent start date,
    then, depending on the periodic rent adjustment type, every 20 or 10 years thereafter.
    """
    start_year = get_tasotarkistus_start_year(rent)
    current_year = timezone.now().year
    years_since_start = current_year - start_year
    adjustment_type = rent.periodic_rent_adjustment_type

    if years_since_start < 20:
        return False

    if adjustment_type == PeriodicRentAdjustmentType.TASOTARKISTUS_20_20:
        return years_since_start >= 20 and (years_since_start - 20) % 20 == 0

    elif adjustment_type == PeriodicRentAdjustmentType.TASOTARKISTUS_20_10:
        return years_since_start >= 20 and (years_since_start - 20) % 10 == 0

    else:
        raise ValueError(f"Unknown periodic rent adjustment type: {adjustment_type}")


def get_tasotarkistus_start_year(rent: Rent) -> int:
    """
    Get the starting year for the rent, as relates to tasotarkistus calculation.

    The most reliable source should be the rent's own stored starting point figure year,
    because it is explicitly meant for this purpose in tasotarkistus calculation.
    """
    if rent.start_price_index_point_figure_year is not None:
        # The initial year is explicitly stored in the rent, so use it.
        return rent.start_price_index_point_figure_year

    # The starting point figure year is missing from rent. This is an error.
    # It should have been set when the rent was created as a duplicate
    # data point in addition to the database table for point figures.
    #
    # Still, we might be able to substitute with the rent's start date year.
    # NOTE in future: is this a reliable substitute?
    elif rent.start_date is not None:
        return rent.start_date.year

    else:
        raise ValueError(
            "Rent does not have a starting year or starting point figure year."
            " Cannot proceed with calculation."
        )


def get_tasotarkistus_point_figure_start_value(rent: Rent, start_year: int) -> Decimal:
    """
    Get the starting point figure value for the rent.

    The most reliable source should be the rent's own stored starting point
    figure value, but we can substitute it with a database lookup if necessary.
    """
    if rent.start_price_index_point_figure_value is not None:
        # The initial value is explicitly stored in the rent, so use it.
        return rent.start_price_index_point_figure_value

    # The starting point figure value is missing from rent. This is an error.
    # It should have been set when the rent was created as a duplicate
    # data point in addition to the database table for point figures.
    #
    # Still, we might be able to substitute with a database lookup of the
    # price index point figure.

    price_index = rent.old_dwellings_in_housing_companies_price_index
    if not price_index:
        raise ValueError(
            "Rent does not have an associated price index."
            "Cannot proceed with calculation."
        )

    error_message = (
        f"Starting point figure value for rent {rent.pk}, index "
        f"{price_index.pk}, year {start_year} is not available."
        " Cannot proceed with calculation."
    )
    try:
        point_figure = IndexPointFigureYearly.objects.get(
            index=price_index,
            year=start_year,
        )
        if point_figure.value is not None:
            return point_figure.value
        else:
            raise ValueError(error_message)
    except IndexPointFigureYearly.DoesNotExist:
        raise ValueError(error_message)


def get_old_rent_amount(rent: Rent) -> Decimal:
    """
    Fetches the old rent amount.

    In this example, we use leasing.models.rent.FixedInitialYearRent.amount.
    """
    today = get_today()
    beginning_of_this_month = today.replace(day=1)
    end_of_this_month = today + relativedelta(days=31)
    is_active_q = q_is_active_in_period(
        start_date=beginning_of_this_month,
        end_date=end_of_this_month,
    )
    fixed_initial_year_rent = (
        FixedInitialYearRent.objects.filter(rent=rent).filter(is_active_q).first()
    )
    if fixed_initial_year_rent is None:
        raise ValueError("No active FixedInitialYearRent found for the rent.")

    return fixed_initial_year_rent.amount


def get_today() -> datetime.date:
    """Helper function to make testing easier."""
    return timezone.now().date()


def q_is_active_in_period(start_date: datetime.date, end_date: datetime.date) -> Q:
    """Returns a Q object to filter objects active in the given period."""
    return Q(Q(end_date=None) | Q(end_date__gte=start_date)) & Q(
        Q(start_date=None) | Q(start_date__lte=end_date)
    )


def get_custom_consideration_percentage(_: Rent) -> Decimal:
    """
    Fetches any custom consideration percentage for the rent.

    The City of Helsinki reserves the right to apply custom considerations on
    a case-by-case basis.

    In this example, we assume a fixed 50% consideration for illustration purposes.
    This means that only 50% of the calculated adjustment is applied.
    """
    return Decimal("50")


def calculate_new_rent_amount_after_periodic_rent_adjustment(
    # TODO parameters
    rent_amount: Decimal,
    price_index: OldDwellingsInHousingCompaniesPriceIndex,
    adjustment_type: PeriodicRentAdjustmentType,
    tasotarkistus_start_year: int,
    tasotarkistus_point_figure_start_value: Decimal,
    custom_consideration_percentage: Decimal = Decimal("100"),
    # TODO something for custom considerations("only 50% this time...")? how to represent?
) -> Decimal:
    """
    TODO understand how calculation works
    TODO explain here, then  write the actual calculation
    TODO explain parameters
    """

    # TODO determine which adjustment number this is (first, second, etc.).

    maximum_adjustment_percentage = get_maximum_adjustment_percentage(
        adjustment_type, tasotarkistus_start_year
    )

    # TODO fetch 3 previous years' index point figures for calculation
    # TODO calculate average point figure value
    # TODO calculate adjustment based on average and starting value
    # TODO clamp the adjustment to maximum allowed by the allowed percentage
    # TODO apply custom considerations as per parameters (e.g. "only 50% this time")

    # TODO implement

    return Decimal(0.0)  # TODO fix return value


def get_maximum_adjustment_percentage(
    adjustment_type: PeriodicRentAdjustmentType,
    tasotarkistus_start_year: int,
) -> Decimal:
    """
    Get the maximum adjustment percentage based on the periodic rent adjustment type.

    First adjustment is always at 20 years after start year.
    Maximum adjustment is 50% for the first adjustment.

    Subsequent adjustments depend on adjustment type (every 10 or 20 years).
    """
    this_year = get_today().year
    years_since_start = this_year - tasotarkistus_start_year

    if years_since_start == 20:
        return Decimal(50)
    else:
        # Assumes that is_correct_year_for_tasotarkistus has already been called
        # and returned True, so this is a subsequent adjustment year.
        return get_maximum_subsequent_adjustment_percentage(adjustment_type)


def get_maximum_subsequent_adjustment_percentage(
    adjustment_type: PeriodicRentAdjustmentType,
) -> Decimal:
    """
    Get the maximum subsequent adjustment percentage based on the periodic rent adjustment type.

    Meaning, for adjustments after the first one at 20 years.
    """
    if adjustment_type == PeriodicRentAdjustmentType.TASOTARKISTUS_20_20:
        return Decimal(50)
    elif adjustment_type == PeriodicRentAdjustmentType.TASOTARKISTUS_20_10:
        return Decimal(25)
    else:
        raise ValueError(f"Unknown periodic rent adjustment type: {adjustment_type}")
