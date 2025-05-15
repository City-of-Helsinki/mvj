import datetime
import logging
from decimal import ROUND_HALF_UP, Decimal

from auditlog.registry import auditlog
from dateutil.relativedelta import relativedelta
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q, QuerySet
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy
from enumfields import EnumField

from field_permissions.registry import field_permissions
from leasing.calculation.index import IndexCalculation, LegacyIndexCalculation
from leasing.calculation.result import (
    CalculationAmount,
    CalculationNote,
    CalculationResult,
    FixedInitialYearRentCalculationResult,
)
from leasing.enums import (
    AreaUnit,
    BasisOfRentType,
    BasisOfRentZone,
    DueDatesPosition,
    DueDatesType,
    IndexType,
    PeriodicRentAdjustmentType,
    PeriodType,
    RentAdjustmentAmountType,
    RentAdjustmentType,
    RentCycle,
    RentType,
    SubventionType,
)
from leasing.models.types import BillingPeriod, TemporarySubventionItem
from leasing.models.utils import (
    DayMonth,
    fix_amount_for_overlap,
    get_billing_periods_for_year,
    get_date_range_amount_from_monthly_amount,
    get_monthly_amount_by_period_type,
    get_range_overlap_and_remainder,
    group_items_in_period_by_date_range,
    is_date_on_first_quarter,
    subtract_range_from_range,
    subtract_ranges_from_ranges,
)
from users.models import User

from .decision import Decision
from .mixins import (
    ArchivableModel,
    NameModel,
    TimeStampedModel,
    TimeStampedSafeDeleteModel,
)

first_day_of_every_month = []

for i in range(1, 13):
    first_day_of_every_month.append(DayMonth(day=1, month=i))

FIXED_DUE_DATES: dict[str, dict[int, list[DayMonth]]] = {
    DueDatesPosition.START_OF_MONTH: {
        1: [DayMonth(day=2, month=1)],
        2: [DayMonth(day=2, month=1), DayMonth(day=1, month=7)],
        4: [
            DayMonth(day=2, month=1),
            DayMonth(day=1, month=4),
            DayMonth(day=1, month=7),
            DayMonth(day=1, month=10),
        ],
        12: first_day_of_every_month,
    },
    DueDatesPosition.MIDDLE_OF_MONTH: {
        1: [DayMonth(day=30, month=6)],
        2: [DayMonth(day=15, month=3), DayMonth(day=30, month=9)],
        4: [
            DayMonth(day=1, month=3),
            DayMonth(day=15, month=4),
            DayMonth(day=15, month=7),
            DayMonth(day=15, month=10),
        ],
        12: first_day_of_every_month,
    },
}

logger = logging.getLogger(__name__)


class RentIntendedUse(NameModel):
    """
    In Finnish: Käyttötarkoitus
    """

    class Meta(NameModel.Meta):
        verbose_name = pgettext_lazy("Model name", "Rent intended use")
        verbose_name_plural = pgettext_lazy("Model name", "Rent intended uses")


class OldDwellingsInHousingCompaniesPriceIndex(TimeStampedModel):
    """
    In Finnish: Vanhojen osakeasuntojen hintaindeksi

    From my understanding, a unique price index is identified by the API
    database table URL and code of the index. A single table can hold multiple
    indexes, and a single code can be used in multiple tables.

    Members:
        code: Code for the index's table column. Example: "ketj_P_QA_T". \
              Same code is shared between tables for different intervals, e.g. \
              yearly or quarterly.
        name: Name of the index. Example: "Index (2020=100)".
        comment: Comment for the index's table column.
        source: Source of the data.
        source_table_updated: UTC timestamp when the source table was last updated.
        source_table_label: Label for the source table.
        url: API endpoint URL.
    """

    # Maximum lengths are arbitrary, but set to avoid extra large input.
    CHARFIELD_MAX_LENGTH = 255

    code = models.CharField(
        verbose_name=_("Index code"),
        max_length=CHARFIELD_MAX_LENGTH,
        unique=True,
    )
    name = models.CharField(
        verbose_name=_("Index name"),
        max_length=CHARFIELD_MAX_LENGTH,
    )
    comment = models.TextField(verbose_name=_("Region"), blank=True)
    source = models.CharField(
        verbose_name=_("Data source"),
        blank=True,
        max_length=CHARFIELD_MAX_LENGTH,
    )
    source_table_updated = models.DateTimeField(
        verbose_name=_("Source table updated"), null=True
    )
    source_table_label = models.TextField(
        verbose_name=_("Source table label"),
        blank=True,
    )
    url = models.CharField(
        verbose_name=_("API endpoint URL"),
        max_length=CHARFIELD_MAX_LENGTH,
    )

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name = pgettext_lazy(
            "model name", "price index of old dwellings in housing companies"
        )
        verbose_name_plural = pgettext_lazy(
            "model name", "price indexes of old dwellings in housing companies"
        )


class Rent(TimeStampedSafeDeleteModel):
    """
    In Finnish: Vuokran perustiedot
    """

    lease = models.ForeignKey(
        "leasing.Lease",
        verbose_name=_("Lease"),
        related_name="rents",
        on_delete=models.PROTECT,
    )

    # In Finnish: Vuokralaji
    type = EnumField(RentType, verbose_name=_("Type"), max_length=30)

    # In Finnish: Vuokrakausi
    cycle = EnumField(
        RentCycle, verbose_name=_("Cycle"), null=True, blank=True, max_length=30
    )

    # In Finnish: Indeksin tunnusnumero
    index_type = EnumField(
        IndexType, verbose_name=_("Index type"), null=True, blank=True, max_length=30
    )

    # In Finnish: Laskutusjako
    due_dates_type = EnumField(
        DueDatesType,
        verbose_name=_("Due dates type"),
        null=True,
        blank=True,
        max_length=30,
    )

    # In Finnish: Laskut kpl / vuodessa
    due_dates_per_year = models.PositiveIntegerField(
        verbose_name=_("Due dates per year"), null=True, blank=True
    )

    # In Finnish: Perusindeksi
    elementary_index = models.PositiveIntegerField(
        verbose_name=_("Elementary index"), null=True, blank=True
    )

    # In Finnish: Pyöristys
    index_rounding = models.PositiveIntegerField(
        verbose_name=_("Index rounding"), null=True, blank=True
    )

    # In Finnish: X-luku
    x_value = models.PositiveIntegerField(
        verbose_name=_("X value"), null=True, blank=True
    )

    # In Finnish: Y-luku
    y_value = models.PositiveIntegerField(
        verbose_name=_("Y value"), null=True, blank=True
    )

    # In Finnish: Y-alkaen
    y_value_start = models.DateField(
        verbose_name=_("Y value start date"), null=True, blank=True
    )

    # In Finnish: Tasaus alkupvm
    equalization_start_date = models.DateField(
        verbose_name=_("Equalization start date"), null=True, blank=True
    )

    # In Finnish: Tasaus loppupvm
    equalization_end_date = models.DateField(
        verbose_name=_("Equalization end date"), null=True, blank=True
    )

    # In Finnish: Määrä (vain kun tyyppi on kertakaikkinen vuokra)
    amount = models.DecimalField(
        verbose_name=_("Amount"), null=True, blank=True, max_digits=10, decimal_places=2
    )

    # In Finnish: Kommentti
    note = models.TextField(verbose_name=_("Note"), null=True, blank=True)

    # In Finnish: Alkupvm
    start_date = models.DateField(verbose_name=_("Start date"), null=True, blank=True)

    # In Finnish: Loppupvm
    end_date = models.DateField(verbose_name=_("End date"), null=True, blank=True)

    # These ratios are used if the rent type is MANUAL
    # manual_ratio is used for the whole year if the RentCycle is
    # JANUARY_TO_DECEMBER. If the Rent Cycle is APRIL_TO_MARCH, this is used for 1.4. - 31.12.
    # In Finnish: Kerroin (Käsinlaskenta)
    manual_ratio = models.DecimalField(
        verbose_name=_("Manual ratio"),
        null=True,
        blank=True,
        max_digits=10,
        decimal_places=2,
    )

    # If the Rent Cycle is APRIL_TO_MARCH, manual_ratio_previous is used for 1.1. - 31.3.
    # In Finnish: Aiempi kerroin (Käsinlaskenta)
    manual_ratio_previous = models.DecimalField(
        verbose_name=_("Manual ratio (previous)"),
        null=True,
        blank=True,
        max_digits=10,
        decimal_places=2,
    )

    # In Finnish: Perittävä vuokramäärä
    payable_rent_amount = models.DecimalField(
        verbose_name=_("Payable rent amount"),
        null=True,
        blank=True,
        max_digits=10,
        decimal_places=2,
    )

    # In Finnish: Perittävän vuokramäärän aloituspäivä
    payable_rent_start_date = models.DateField(
        verbose_name=_("Payable rent start date"),
        null=True,
        blank=True,
    )

    # In Finnish: Perittävän vuokramäärän päättymispäivä
    payable_rent_end_date = models.DateField(
        verbose_name=_("Payable rent end date"), null=True, blank=True
    )

    # In Finnish: Korvaava saamislaji
    # Choices should be filtered by the lease's service unit
    override_receivable_type = models.ForeignKey(
        "leasing.ReceivableType",
        verbose_name=_("Override receivable type"),
        related_name="+",
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )

    # In Finnish: Tasotarkistusindeksi
    # Is used as indicator that the rent uses periodic rent adjustment.
    old_dwellings_in_housing_companies_price_index = models.ForeignKey(
        OldDwellingsInHousingCompaniesPriceIndex,
        verbose_name=_("Old dwellings in housing companies price index"),
        related_name="+",
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )

    # In Finnish: Tasotarkistuksen tyyppi
    periodic_rent_adjustment_type = EnumField(
        PeriodicRentAdjustmentType,
        verbose_name=_("Periodic Rent Adjustment Type"),
        null=True,
        blank=True,
        max_length=20,
    )

    # In Finnish: Tasotarkistusindeksin pisteluku vuokran alkaessa (edellisen vuoden keskiarvo)
    start_price_index_point_figure_value = models.DecimalField(
        verbose_name=_("Start price index point figure value"),
        decimal_places=1,
        max_digits=8,
        null=True,
    )

    # In Finnish: Tasotarkistusindeksin pisteluvun vuosi vuokran alkaessa (edellinen vuosi)
    start_price_index_point_figure_year = models.PositiveSmallIntegerField(
        verbose_name=_("Start price index point figure year"),
        null=True,
    )

    recursive_get_related_skip_relations = ["lease"]

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Rent")
        verbose_name_plural = pgettext_lazy("Model name", "Rents")

    def calculate_payable_rent(self):
        if self.cycle is None:
            return

        current_year = datetime.date.today().year
        if self.cycle == RentCycle.JANUARY_TO_DECEMBER:
            start_date = datetime.date(year=current_year, month=1, day=1)
            end_date = datetime.date(year=current_year, month=12, day=31)
        elif self.cycle == RentCycle.APRIL_TO_MARCH:
            start_date = datetime.date(year=current_year, month=4, day=1)
            end_date = datetime.date(year=current_year + 1, month=3, day=31)
        else:
            logger.warning(
                _(
                    "Cannot calculate payable rent. The rent cycle '{}' is not defined."
                ).format(self.cycle)
            )
            return

        calculation_result = self.get_amount_for_date_range(
            start_date, end_date, dry_run=True
        )

        self.payable_rent_amount = calculation_result.get_total_amount().quantize(
            Decimal(".01"), rounding=ROUND_HALF_UP
        )
        self.payable_rent_start_date = start_date
        self.payable_rent_end_date = end_date

        self.save()

    def get_intended_uses_for_date_range(self, date_range_start, date_range_end):
        intended_uses = set()

        range_filtering = Q(
            Q(Q(end_date=None) | Q(end_date__gte=date_range_start))
            & Q(Q(start_date=None) | Q(start_date__lte=date_range_end))
        )

        intended_uses.update(
            [
                fiyr.intended_use
                for fiyr in self.fixed_initial_year_rents.filter(range_filtering)
            ]
        )
        intended_uses.update(
            [cr.intended_use for cr in self.contract_rents.filter(range_filtering)]
        )

        return intended_uses

    def clamp_date_range(self, date_range_start, date_range_end):
        clamped_date_range_start = date_range_start
        clamped_date_range_end = date_range_end

        if (self.start_date and date_range_start < self.start_date) and (
            not self.end_date or date_range_start < self.end_date
        ):
            clamped_date_range_start = self.start_date

        if (self.end_date and date_range_end > self.end_date) and (
            self.start_date and date_range_end > self.start_date
        ):
            clamped_date_range_end = self.end_date

        return clamped_date_range_start, clamped_date_range_end

    def get_rent_adjustment_amount(self, intended_use, amount, period, dry_run=False):
        calculation_amounts = []

        rent_adjustments = self.get_applicable_adjustments(intended_use, *period)

        total_adjustment_amount = Decimal(0)

        grouped_rent_adjustments = group_items_in_period_by_date_range(
            rent_adjustments, *period
        )

        for adjustment_range, adjustments in grouped_rent_adjustments.items():
            if not adjustments:
                continue

            tmp_amount = fix_amount_for_overlap(
                amount,
                adjustment_range,
                subtract_range_from_range(period, adjustment_range),
            )

            for rent_adjustment in adjustments:
                adjustment_amount = rent_adjustment.get_amount_for_date_range(
                    tmp_amount,
                    *adjustment_range,
                    update_amount_total=False if dry_run else True,
                )

                total_adjustment_amount += adjustment_amount.amount
                tmp_amount += adjustment_amount.amount

                calculation_amounts.append(adjustment_amount)

        return calculation_amounts

    def fixed_initial_year_rent_amount_for_date_range(
        self, intended_use, date_range_start, date_range_end, dry_run=False
    ):
        fixed_initial_year_rents: QuerySet[FixedInitialYearRent] = (
            self.fixed_initial_year_rents.filter(
                Q(
                    Q(Q(end_date=None) | Q(end_date__gte=date_range_start))
                    & Q(Q(start_date=None) | Q(start_date__lte=date_range_end))
                )
                & Q(intended_use=intended_use)
            )
        )

        calculation_result = FixedInitialYearRentCalculationResult(
            date_range_start=date_range_start, date_range_end=date_range_end
        )

        for fixed_initial_year_rent in fixed_initial_year_rents:
            (fixed_overlap, fixed_remainders) = get_range_overlap_and_remainder(
                date_range_start, date_range_end, *fixed_initial_year_rent.date_range
            )

            if not fixed_overlap:
                continue

            calculation_result.applied_ranges.append(fixed_overlap)

            fixed_amount = fixed_initial_year_rent.get_amount_for_date_range(
                *fixed_overlap
            )

            rent_adjustment_amounts = self.get_rent_adjustment_amount(
                fixed_initial_year_rent.intended_use,
                fixed_amount.amount,
                fixed_overlap,
                dry_run=dry_run,
            )
            fixed_amount.add_sub_amounts(rent_adjustment_amounts)

            calculation_result.add_amount(fixed_amount)

        if calculation_result.applied_ranges:
            calculation_result.remaining_ranges = subtract_ranges_from_ranges(
                [(date_range_start, date_range_end)], calculation_result.applied_ranges
            )

        return calculation_result

    def contract_rent_amount_for_date_range(  # noqa: TODO
        self, intended_use, date_range_start, date_range_end, dry_run=False
    ):
        calculation_result = CalculationResult(
            date_range_start=date_range_start, date_range_end=date_range_end
        )

        contract_rents: QuerySet[ContractRent] = self.contract_rents.filter(
            Q(
                Q(Q(end_date=None) | Q(end_date__gte=date_range_start))
                & Q(Q(start_date=None) | Q(start_date__lte=date_range_end))
            )
            & Q(intended_use=intended_use)
        )

        for contract_rent in contract_rents:
            (contract_overlap, _remainder) = get_range_overlap_and_remainder(
                date_range_start, date_range_end, *contract_rent.date_range
            )

            if not contract_overlap:
                continue

            if self.type == RentType.FREE:
                continue
            elif self.type == RentType.FIXED:
                contract_amount = contract_rent.get_amount_for_date_range(
                    *contract_overlap
                )
            elif self.type == RentType.MANUAL:
                contract_amount = contract_rent.get_base_amount_for_date_range(
                    *contract_overlap
                )

                manual_ratio = self.manual_ratio

                if self.cycle == RentCycle.APRIL_TO_MARCH and is_date_on_first_quarter(
                    contract_overlap[0]
                ):
                    manual_ratio = self.manual_ratio_previous

                if manual_ratio:
                    contract_amount.amount *= manual_ratio
                    contract_amount.add_note(
                        CalculationNote(
                            type="ratio",
                            description=_("Manual ratio {ratio}").format(
                                ratio=manual_ratio
                            ),
                        )
                    )
                else:
                    contract_amount.amount = Decimal(0)
                    contract_amount.add_note(
                        CalculationNote(
                            type="notice", description=_("Manual ratio not found!")
                        )
                    )
            elif self.type == RentType.INDEX or self.type == RentType.INDEX2022:
                contract_amount = contract_rent.get_base_amount_for_date_range(
                    *contract_overlap
                )

                index = self.get_index_for_date(contract_overlap[0])

                if self.type == RentType.INDEX:
                    # Index calculation which is used in rents before November 2022
                    index_calculation = LegacyIndexCalculation(
                        amount=contract_amount.amount,
                        index=index,
                        index_type=self.index_type,
                        precision=self.index_rounding,
                        x_value=self.x_value,
                        y_value=self.y_value,
                    )
                elif self.type == RentType.INDEX2022:
                    # New Index calculation for rents after November 2022
                    index_calculation = IndexCalculation(
                        amount=contract_amount.amount,
                        current_index=index,
                        rent_index=contract_rent.index,
                    )

                # There are some internal, no-cost INDEX rents which have no IndexType.
                # For them we simply return the amount without index correction.
                try:
                    contract_amount.amount = index_calculation.calculate()
                except NotImplementedError:
                    pass

                for note in index_calculation.notes:
                    contract_amount.add_note(note)

                # Create a notice if the index used is older than it should be.
                # (The previous years average index is not yet available)
                if not self.is_correct_index_for_date(index, contract_overlap[0]):
                    contract_amount.add_note(
                        CalculationNote(
                            type="notice",
                            description=_(
                                "Average index for the year {} is not available!"
                            ).format(
                                self.get_rent_year_for_date(contract_overlap[0]) - 1
                            ),
                        )
                    )
            else:
                raise NotImplementedError(
                    "RentType {} not implemented".format(self.type)
                )

            rent_adjustment_amounts = self.get_rent_adjustment_amount(
                intended_use, contract_amount.amount, contract_overlap, dry_run=dry_run
            )
            contract_amount.add_sub_amounts(rent_adjustment_amounts)

            calculation_result.add_amount(contract_amount)

        return calculation_result

    def get_amount_for_date_range(
        self, date_range_start, date_range_end, explain=False, dry_run=False
    ):  # noqa: TODO
        calculation_result = CalculationResult(
            date_range_start=date_range_start, date_range_end=date_range_end
        )

        if self.type == RentType.ONE_TIME:
            # ONE_TIME rents are calculated manually
            return calculation_result

        # Limit the date range based on the rent start and end dates
        (clamped_date_range_start, clamped_date_range_end) = self.clamp_date_range(
            date_range_start, date_range_end
        )

        # Calculate rent separately for every intended use
        for intended_use in self.get_intended_uses_for_date_range(
            clamped_date_range_start, clamped_date_range_end
        ):
            fixed_initial_year_rent_calculation_result = (
                self.fixed_initial_year_rent_amount_for_date_range(
                    intended_use,
                    clamped_date_range_start,
                    clamped_date_range_end,
                    dry_run=dry_run,
                )
            )

            calculation_result.combine(fixed_initial_year_rent_calculation_result)

            # Fixed initial year rent overrides contract rent. Therefore
            # if there are fixed initial year rents for the whole date range,
            # there is no need to calculate the contract rents.
            if fixed_initial_year_rent_calculation_result.is_range_fully_applied():
                continue

            # Otherwise calculate contract rents for the remaining date ranges
            # or for the whole range
            if fixed_initial_year_rent_calculation_result.applied_ranges:
                date_ranges = (
                    fixed_initial_year_rent_calculation_result.remaining_ranges
                )
            else:
                date_ranges = [(clamped_date_range_start, clamped_date_range_end)]

            # We may need to calculate multiple separate ranges if the rent
            # type is index or manual because the index number could be different
            # in different years.
            if self.type in [RentType.INDEX, RentType.MANUAL]:
                date_ranges = self.split_ranges_by_cycle(date_ranges)

            for range_start, range_end in date_ranges:
                contract_rent_calculation_result = (
                    self.contract_rent_amount_for_date_range(
                        intended_use, range_start, range_end, dry_run=dry_run
                    )
                )

                calculation_result.combine(contract_rent_calculation_result)

        return calculation_result

    def get_applicable_adjustments(
        self, intended_use, date_range_start, date_range_end
    ) -> list["RentAdjustment"]:
        applicable_adjustments = []

        range_filtering = Q(
            Q(Q(end_date=None) | Q(end_date__gte=date_range_start))
            & Q(Q(start_date=None) | Q(start_date__lte=date_range_end))
        )

        for rent_adjustment in self.rent_adjustments.filter(range_filtering):
            if rent_adjustment.intended_use != intended_use:
                continue

            (
                adjustment_overlap,
                adjustment_remainders,
            ) = get_range_overlap_and_remainder(
                date_range_start, date_range_end, *rent_adjustment.date_range
            )

            if not adjustment_overlap:
                continue

            applicable_adjustments.append(rent_adjustment)

        return applicable_adjustments

    def get_custom_due_dates_as_daymonths(self) -> list[DayMonth]:
        if self.due_dates_type != DueDatesType.CUSTOM:
            return []

        due_dates: QuerySet[RentDueDate] = self.due_dates
        return [dd.as_daymonth() for dd in due_dates.all().order_by("month", "day")]

    def get_due_dates_as_daymonths(self) -> list[DayMonth]:
        due_dates = []
        if self.due_dates_type == DueDatesType.FIXED:
            # TODO: handle unknown due date count
            if self.due_dates_per_year in (1, 2, 4, 12):
                due_dates_position = self.lease.type.due_dates_position

                # Fixed rent due dates are always start of month regardless of lease type
                if self.type == RentType.FIXED:
                    due_dates_position = DueDatesPosition.START_OF_MONTH

                due_dates = FIXED_DUE_DATES[due_dates_position][self.due_dates_per_year]
        elif self.due_dates_type == DueDatesType.CUSTOM:
            due_dates = self.get_custom_due_dates_as_daymonths()

        return due_dates

    def get_due_dates_for_period(
        self, start_date: datetime.date, end_date: datetime.date
    ) -> list[datetime.date]:
        rent_due_dates = self.get_due_dates_as_daymonths()

        due_dates: list[datetime.date] = []
        for rent_due_date in rent_due_dates:
            for year in range(start_date.year, end_date.year + 1):
                tmp_date = datetime.date(
                    year=year, month=rent_due_date.month, day=rent_due_date.day
                )
                if start_date <= tmp_date <= end_date:
                    due_dates.append(tmp_date)

        return due_dates

    def get_billing_period_from_due_date(
        self, due_date: datetime.date
    ) -> BillingPeriod | None:
        if not due_date:
            return None

        due_dates_per_year = self.get_due_dates_for_period(
            datetime.date(year=due_date.year, month=1, day=1),
            datetime.date(year=due_date.year, month=12, day=31),
        )

        try:
            due_date_index = due_dates_per_year.index(due_date)

            return get_billing_periods_for_year(due_date.year, len(due_dates_per_year))[
                due_date_index
            ]
        except (ValueError, IndexError):
            # TODO: better error handling
            return None

    def get_all_billing_periods_for_year(self, year: int) -> list[BillingPeriod | None]:
        date_range_start = datetime.date(year, 1, 1)
        date_range_end = datetime.date(year, 12, 31)

        billing_periods: list[BillingPeriod | None] = []
        for due_date in self.get_due_dates_for_period(date_range_start, date_range_end):
            billing_periods.append(self.get_billing_period_from_due_date(due_date))

        return billing_periods

    def is_the_last_billing_period(self, billing_period: BillingPeriod):
        billing_periods = self.get_all_billing_periods_for_year(billing_period[0].year)

        try:
            return billing_periods.index(billing_period) == len(billing_periods) - 1
        except ValueError:
            return False

    def split_range_by_cycle(self, date_range_start, date_range_end):
        if not self.cycle:
            return [(date_range_start, date_range_end)]

        ranges = [(date_range_start, date_range_end)]
        years = range(date_range_start.year, date_range_end.year + 1)

        for year in years:
            if self.cycle == RentCycle.APRIL_TO_MARCH:
                cycle_change_date = datetime.date(year=year, month=4, day=1)
            else:
                cycle_change_date = datetime.date(year=year, month=1, day=1)

            for i, (range_start_date, range_end_date) in enumerate(ranges):
                if range_start_date < cycle_change_date < range_end_date:
                    del ranges[i]
                    ranges.extend(
                        [
                            (
                                range_start_date,
                                cycle_change_date - relativedelta(days=1),
                            ),
                            (cycle_change_date, range_end_date),
                        ]
                    )

        return ranges

    def split_ranges_by_cycle(self, ranges):
        if not self.cycle or self.cycle != RentCycle.APRIL_TO_MARCH:
            return ranges

        new_ranges = []
        for one_range in ranges:
            new_ranges.extend(self.split_range_by_cycle(*one_range))

        return new_ranges

    def get_rent_year_for_date(self, the_date):
        """Returns the year on which the_date is considered to land on
        regarding this rent. i.e. if the billing cycle is from april to march
        the start of the year is considered to be part of the previous years rent"""
        if self.cycle == RentCycle.APRIL_TO_MARCH and is_date_on_first_quarter(
            the_date
        ):
            return the_date.year - 1

        return the_date.year

    def get_index_for_date(self, the_date):
        return Index.objects.get_latest_for_year(self.get_rent_year_for_date(the_date))

    def is_correct_index_for_date(self, index, the_date):
        """Check if the provided index is the previous years average index"""
        correct_year = self.get_rent_year_for_date(the_date) - 1

        return index.month is None and index.year == correct_year

    def is_active_on_period(self, date_range_start, date_range_end):
        if (self.end_date is None or self.end_date >= date_range_start) and (
            self.start_date is None or self.start_date <= date_range_end
        ):
            return True

        return False

    def set_start_price_index_point_figure(self):
        """Sets the values for Periodic Rent Adjustment's price index's
        point figure at the start of the rent.

        Once set, they should not be changed afterwards."""
        if not self.old_dwellings_in_housing_companies_price_index:
            # The rent does not use a Periodic Rent Adjustment.
            return

        if (
            self.start_price_index_point_figure_value is not None
            and self.start_price_index_point_figure_year is not None
        ):
            # The required values are already set and should not be changed.
            return

        try:
            point_figure = IndexPointFigureYearly.objects.get(
                index=self.old_dwellings_in_housing_companies_price_index,
                year=self.lease.start_date.year - 1,
            )
            self.start_price_index_point_figure_value = point_figure.value
            self.start_price_index_point_figure_year = point_figure.year
        except IndexPointFigureYearly.DoesNotExist:
            # The details will be added to this rent later via a batchjob
            # when the data becomes available in the source API.
            return


class RentDueDate(TimeStampedSafeDeleteModel):
    """
    In Finnish: Eräpäivä
    """

    rent = models.ForeignKey(
        Rent, verbose_name=_("Rent"), related_name="due_dates", on_delete=models.CASCADE
    )
    day = models.IntegerField(
        verbose_name=_("Day"), validators=[MinValueValidator(1), MaxValueValidator(31)]
    )
    month = models.IntegerField(
        verbose_name=_("Month"),
        validators=[MinValueValidator(1), MaxValueValidator(12)],
    )

    recursive_get_related_skip_relations = ["rent"]

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Rent due date")
        verbose_name_plural = pgettext_lazy("Model name", "Rent due dates")

    def as_daymonth(self):
        return DayMonth(day=self.day, month=self.month)


class FixedInitialYearRent(TimeStampedSafeDeleteModel):
    """
    In Finnish: Kiinteä alkuvuosivuokra
    """

    rent = models.ForeignKey(
        Rent,
        verbose_name=_("Rent"),
        related_name="fixed_initial_year_rents",
        on_delete=models.CASCADE,
    )

    # In Finnish: Vuokra
    amount = models.DecimalField(
        verbose_name=_("Amount"), max_digits=10, decimal_places=2
    )

    # In Finnish: Käyttötarkoitus
    intended_use = models.ForeignKey(
        RentIntendedUse,
        verbose_name=_("Intended use"),
        related_name="+",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )

    # In Finnish: Alkupvm
    start_date = models.DateField(verbose_name=_("Start date"), null=True, blank=True)

    # In Finnish: Loppupvm
    end_date = models.DateField(verbose_name=_("End date"), null=True, blank=True)

    recursive_get_related_skip_relations = ["rent"]

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Fixed initial year rent")
        verbose_name_plural = pgettext_lazy("Model name", "Fixed initial year rents")

    @property
    def date_range(self):
        return self.start_date, self.end_date

    def get_amount_for_date_range(self, date_range_start, date_range_end):
        if self.start_date:
            date_range_start = max(self.start_date, date_range_start)
        if self.end_date:
            date_range_end = min(self.end_date, date_range_end)

        if date_range_start > date_range_end:
            return False

        monthly_amount = self.amount / 12
        date_range_amount = get_date_range_amount_from_monthly_amount(
            monthly_amount, date_range_start, date_range_end, real_month_lengths=False
        )

        calculation_amount = CalculationAmount(
            item=self,
            date_range_start=date_range_start,
            date_range_end=date_range_end,
            amount=date_range_amount,
        )

        return calculation_amount


class ContractRent(TimeStampedSafeDeleteModel):
    """
    In Finnish: Sopimusvuokra
    """

    rent = models.ForeignKey(
        Rent,
        verbose_name=_("Rent"),
        related_name="contract_rents",
        on_delete=models.CASCADE,
    )

    # If rent.type is INDEX2022:
    # In Finnish: Alkuvuosivuokra (ind)
    # (index from the index column)
    # If rent.type is INDEX:
    # In Finnish: Sopimusvuokra (ind 100)
    amount = models.DecimalField(
        verbose_name=_("Amount"), max_digits=10, decimal_places=2
    )

    # In Finnish: Yksikkö
    period = EnumField(PeriodType, verbose_name=_("Period"), max_length=30)

    # In Finnish: Käyttötarkoitus
    intended_use = models.ForeignKey(
        RentIntendedUse,
        verbose_name=_("Intended use"),
        related_name="+",
        on_delete=models.PROTECT,
    )

    # In Finnish: Indeksi
    index = models.ForeignKey(
        "leasing.Index",
        verbose_name=_("Index"),
        related_name="+",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )

    # In Finnish: Vuokranlaskennan perusteena oleva vuokra
    base_amount = models.DecimalField(
        verbose_name=_("Base amount"),
        max_digits=10,
        decimal_places=2,
    )

    # In Finnish: Yksikkö
    base_amount_period = EnumField(
        PeriodType,
        verbose_name=_("Base amount period"),
        max_length=30,
    )

    # In Finnish: Uusi perusvuosi vuokra
    base_year_rent = models.DecimalField(
        verbose_name=_("Base year rent"),
        null=True,
        blank=True,
        max_digits=10,
        decimal_places=2,
    )

    # In Finnish: Alkupvm
    start_date = models.DateField(verbose_name=_("Start date"), null=True, blank=True)

    # In Finnish: Loppupvm
    end_date = models.DateField(verbose_name=_("End date"), null=True, blank=True)

    recursive_get_related_skip_relations = ["rent"]

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Contract rent")
        verbose_name_plural = pgettext_lazy("Model name", "Contract rents")

    @property
    def date_range(self):
        return self.start_date, self.end_date

    def _get_amount_for_date_range(self, date_range_start, date_range_end, amount_type):
        """
        :param amount_type: "amount" or "base_amount"
        :type amount_type: str
        """
        assert amount_type in ["amount", "base_amount"]

        if self.start_date:
            date_range_start = max(self.start_date, date_range_start)
        if self.end_date:
            date_range_end = min(self.end_date, date_range_end)

        if date_range_start > date_range_end:
            return Decimal("0.00")

        if amount_type == "amount":
            monthly_amount = get_monthly_amount_by_period_type(self.amount, self.period)
        else:
            monthly_amount = get_monthly_amount_by_period_type(
                self.base_amount, self.base_amount_period
            )

        date_range_amount = get_date_range_amount_from_monthly_amount(
            monthly_amount, date_range_start, date_range_end
        )

        calculation_amount = CalculationAmount(
            item=self,
            date_range_start=date_range_start,
            date_range_end=date_range_end,
            amount=date_range_amount,
        )

        return calculation_amount

    def get_amount_for_date_range(self, date_range_start, date_range_end):
        return self._get_amount_for_date_range(
            date_range_start, date_range_end, "amount"
        )

    def get_base_amount_for_date_range(self, date_range_start, date_range_end):
        return self._get_amount_for_date_range(
            date_range_start, date_range_end, "base_amount"
        )


class IndexAdjustedRent(models.Model):
    """
    In Finnish: Indeksitarkistettu vuokra
    """

    rent = models.ForeignKey(
        Rent,
        verbose_name=_("Rent"),
        related_name="index_adjusted_rents",
        on_delete=models.CASCADE,
    )

    # In Finnish: Indeksitarkistettu vuokra
    amount = models.DecimalField(
        verbose_name=_("Amount"), max_digits=10, decimal_places=2
    )

    # In Finnish: Käyttötarkoitus
    intended_use = models.ForeignKey(
        RentIntendedUse,
        verbose_name=_("Intended use"),
        related_name="+",
        on_delete=models.PROTECT,
    )

    # In Finnish: Alkupvm
    start_date = models.DateField(verbose_name=_("Start date"))

    # In Finnish: Loppupvm
    end_date = models.DateField(verbose_name=_("End date"))

    # In Finnish: Laskentak.
    factor = models.DecimalField(
        verbose_name=_("Factor"), max_digits=10, decimal_places=2
    )

    recursive_get_related_skip_relations = ["rent"]

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Index adjusted rent")
        verbose_name_plural = pgettext_lazy("Model name", "Index adjusted rents")


class RentAdjustment(TimeStampedSafeDeleteModel):
    """
    In Finnish: Alennukset ja korotukset
    """

    rent = models.ForeignKey(
        Rent,
        verbose_name=_("Rent"),
        related_name="rent_adjustments",
        on_delete=models.CASCADE,
    )

    # In Finnish: Tyyppi
    type = EnumField(RentAdjustmentType, verbose_name=_("Type"), max_length=30)

    # In Finnish: Käyttötarkoitus
    intended_use = models.ForeignKey(
        RentIntendedUse,
        verbose_name=_("Intended use"),
        related_name="+",
        on_delete=models.PROTECT,
    )

    # In Finnish: Alkupvm
    start_date = models.DateField(verbose_name=_("Start date"), null=True, blank=True)

    # In Finnish: Loppupvm
    end_date = models.DateField(verbose_name=_("End date"), null=True, blank=True)

    # In Finnish: Kokonaismäärä
    full_amount = models.DecimalField(
        verbose_name=_("Full amount"),
        null=True,
        blank=True,
        max_digits=10,
        decimal_places=2,
    )

    # In Finnish: Määrän tyyppi
    amount_type = EnumField(
        RentAdjustmentAmountType, verbose_name=_("Amount type"), max_length=30
    )

    # In Finnish: Jäljellä
    amount_left = models.DecimalField(
        verbose_name=_("Amount left"),
        null=True,
        blank=True,
        max_digits=10,
        decimal_places=2,
    )

    # In Finnish: Päätös
    decision = models.ForeignKey(
        Decision,
        verbose_name=_("Decision"),
        related_name="+",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )

    # In Finnish: Kommentti
    note = models.TextField(verbose_name=_("Note"), null=True, blank=True)

    # In Finnish: Subventiotyyppi
    subvention_type = EnumField(
        SubventionType,
        verbose_name=_("Subvention type"),
        null=True,
        blank=True,
        max_length=30,
    )

    # In Finnish: Markkinavuokran subventio
    subvention_base_percent = models.DecimalField(
        verbose_name=_("Subvention base percent"),
        null=True,
        blank=True,
        max_digits=10,
        decimal_places=2,
    )

    # In Finnish: Siirtymäajan subventio
    subvention_graduated_percent = models.DecimalField(
        verbose_name=_("Graduated subvention percent"),
        null=True,
        blank=True,
        max_digits=10,
        decimal_places=2,
    )

    recursive_get_related_skip_relations = ["rent"]

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Rent adjustment")
        verbose_name_plural = pgettext_lazy("Model name", "Rent adjustments")

    @property
    def date_range(self):
        return self.start_date, self.end_date

    def get_amount_for_date_range(  # NOQA TODO
        self, rent_amount, date_range_start, date_range_end, update_amount_total=False
    ):
        if self.start_date:
            date_range_start = max(self.start_date, date_range_start)
        if self.end_date:
            date_range_end = min(self.end_date, date_range_end)

        if date_range_start > date_range_end:
            return Decimal("0.00")

        if self.amount_type == RentAdjustmentAmountType.PERCENT_PER_YEAR:
            adjustment = self.full_amount / 100 * rent_amount
        elif self.amount_type == RentAdjustmentAmountType.AMOUNT_PER_YEAR:
            adjustment = get_date_range_amount_from_monthly_amount(
                self.full_amount / 12, date_range_start, date_range_end
            )
        elif self.amount_type == RentAdjustmentAmountType.AMOUNT_TOTAL:
            adjustment_left = self.amount_left

            if self.amount_left is None:
                adjustment_left = self.full_amount

            if self.type == RentAdjustmentType.INCREASE:
                adjustment = adjustment_left
            else:
                adjustment = min(adjustment_left, rent_amount)

            if update_amount_total:
                self.amount_left = Decimal(
                    max(0, adjustment_left - adjustment)
                ).quantize(Decimal("0.00"), rounding=ROUND_HALF_UP)
                self.save()
        else:
            raise NotImplementedError(
                "Cannot get adjust amount for RentAdjustmentAmountType {}".format(
                    self.amount_type
                )
            )

        calculation_amount = CalculationAmount(
            item=self,
            amount=Decimal(0),
            date_range_start=date_range_start,
            date_range_end=date_range_end,
        )

        if self.type == RentAdjustmentType.INCREASE:
            calculation_amount.amount = adjustment

            return calculation_amount
        elif self.type == RentAdjustmentType.DISCOUNT:
            calculation_amount.amount = -adjustment

            return calculation_amount
        else:
            raise NotImplementedError(
                "Cannot get adjust amount for RentAdjustmentType {}".format(
                    self.amount_type
                )
            )


class ManagementSubventionFormOfManagement(NameModel):
    """
    In Finnish: Hallintamuoto (Hallintamuotosubventio)
    """

    class Meta(NameModel.Meta):
        verbose_name = pgettext_lazy("Model name", "Form of management (Subvention)")
        verbose_name_plural = pgettext_lazy(
            "Model name", "Form of management (Subvention)"
        )


class ManagementSubvention(models.Model):
    rent_adjustment = models.ForeignKey(
        RentAdjustment,
        verbose_name=_("Rent adjustment"),
        related_name="management_subventions",
        on_delete=models.CASCADE,
    )

    # In Finnish: Hallintamuoto
    management = models.ForeignKey(
        ManagementSubventionFormOfManagement,
        verbose_name=_("Form of management"),
        related_name="+",
        on_delete=models.PROTECT,
    )

    # In Finnish: Subventio markkinavuokrasta / vuosi
    subvention_amount = models.DecimalField(
        verbose_name=_("Subvention amount"), max_digits=10, decimal_places=2
    )

    recursive_get_related_skip_relations = ["rent_adjustment"]

    class Meta:
        verbose_name = pgettext_lazy(
            "Model name", "Management subvention (Rent adjustment)"
        )
        verbose_name_plural = pgettext_lazy(
            "Model name", "Management subventions (Rent adjustment)"
        )


class TemporarySubvention(models.Model):
    rent_adjustment = models.ForeignKey(
        RentAdjustment,
        verbose_name=_("Rent adjustment"),
        related_name="temporary_subventions",
        on_delete=models.CASCADE,
    )

    # In Finnish: Kuvaus
    description = models.CharField(
        verbose_name=_("Description"), null=True, blank=True, max_length=255
    )

    # In Finnish: Subventio markkinavuokrasta prosenttia / vuosi
    subvention_percent = models.DecimalField(
        verbose_name=_("Subvention percent"), max_digits=10, decimal_places=2
    )

    recursive_get_related_skip_relations = ["rent_adjustment"]

    class Meta:
        verbose_name = pgettext_lazy(
            "Model name", "Temporary subvention (Rent adjustment)"
        )
        verbose_name_plural = pgettext_lazy(
            "Model name", "Temporary subventions (Rent adjustment)"
        )


class PayableRent(models.Model):
    """
    In Finnish: Perittävä vuokra
    """

    rent = models.ForeignKey(
        Rent,
        verbose_name=_("Rent"),
        related_name="payable_rents",
        on_delete=models.CASCADE,
    )

    # In Finnish: Perittävä vuokra
    amount = models.DecimalField(
        verbose_name=_("Amount"), max_digits=10, decimal_places=2
    )

    # In Finnish: Alkupvm
    start_date = models.DateField(verbose_name=_("Start date"), null=True, blank=True)

    # In Finnish: Loppupvm
    end_date = models.DateField(verbose_name=_("End date"), null=True, blank=True)

    # In Finnish: Nousu %
    difference_percent = models.DecimalField(
        verbose_name=_("Difference percent"), max_digits=10, decimal_places=2
    )

    # In Finnish: Kalenterivuosivuokra
    calendar_year_rent = models.DecimalField(
        verbose_name=_("Calendar year rent"), max_digits=10, decimal_places=2
    )

    recursive_get_related_skip_relations = ["rent"]

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Payable rent")
        verbose_name_plural = pgettext_lazy("Model name", "Payable rents")


class EqualizedRent(models.Model):
    """
    In Finnish: Tasattu vuokra
    """

    rent = models.ForeignKey(
        Rent,
        verbose_name=_("Rent"),
        related_name="equalized_rents",
        on_delete=models.CASCADE,
    )

    # In Finnish: Alkupvm
    start_date = models.DateField(verbose_name=_("Start date"), null=True, blank=True)

    # In Finnish: Loppupvm
    end_date = models.DateField(verbose_name=_("End date"), null=True, blank=True)

    # In Finnish: Perittävä vuokra
    payable_amount = models.DecimalField(
        verbose_name=_("Payable amount"), max_digits=10, decimal_places=2
    )

    # In Finnish: Tasattu perittävä vuokra
    equalized_payable_amount = models.DecimalField(
        verbose_name=_("Equalized payable amount"), max_digits=10, decimal_places=2
    )

    # In Finnish: Tasauskerroin
    equalization_factor = models.DecimalField(
        verbose_name=_("Equalization factor"), max_digits=8, decimal_places=6
    )

    recursive_get_related_skip_relations = ["rent"]

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Equalized rent")
        verbose_name_plural = pgettext_lazy("Model name", "Equalized rents")


class IndexManager(models.Manager):
    def get_latest_for_date(self, the_date=None):
        """Returns the latest year average index"""
        if the_date is None:
            the_date = datetime.date.today()

        return (
            self.get_queryset()
            .filter(year__lte=the_date.year - 1, month__isnull=True)
            .order_by("-year")
            .first()
        )

    def get_latest_for_year(self, year=None):
        """Returns the latest year average index for year"""
        if year is None:
            year = datetime.date.today().year

        return (
            self.get_queryset()
            .filter(year__lte=year - 1, month__isnull=True)
            .order_by("-year")
            .first()
        )


class Index(models.Model):
    """
    In Finnish: Indeksi
    """

    # In Finnish: Pisteluku (Elinkustannusindeksi 1951:10=100)
    number = models.PositiveIntegerField(verbose_name=_("Number"))

    year = models.PositiveSmallIntegerField(verbose_name=_("Year"))
    month = models.PositiveSmallIntegerField(
        verbose_name=_("Month"),
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(12)],
    )

    objects = IndexManager()

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Index")
        verbose_name_plural = pgettext_lazy("Model name", "Indexes")
        indexes = [models.Index(fields=["year", "month"])]
        unique_together = ("year", "month")
        ordering = ("-year", "-month")

    def __str__(self):
        return _("Index {}{} = {}").format(
            self.year, "/{}".format(self.month) if self.month else "", self.number
        )


class LegacyIndex(models.Model):
    index = models.ForeignKey(
        Index, verbose_name=_("Index"), related_name="+", on_delete=models.CASCADE
    )

    # In Finnish: Pisteluku (Elinkustannusindeksi 1914:1-6=100)
    number_1914 = models.PositiveIntegerField(
        verbose_name=_("Index 1914:1-6=100"), null=True, blank=True
    )

    # In Finnish: Pisteluku (Elinkustannusindeksi 1938:8-1939:7=100)
    number_1938 = models.PositiveIntegerField(
        verbose_name=_("Index 1938:8-1939:7=100"), null=True, blank=True
    )


class IndexPointFigureYearly(TimeStampedModel):
    """
    In Finnish: Indeksipisteluku, vuosittain

    Holds the index point figures.
    Currently only used with the newer price indexes related to Periodic Rent
    Adjustment (Tasotarkistus).

    The yearly index point figure is expected to be the average of all figure
    values from the same year from this same index that use a smaller recording
    inverval.  For example, the yearly index point figure value is the average
    of the year's quarterly values.

    Members:
        index: Reference to the index this point figure is for.
        value: Index point figure value. Example: 101.5.
        year: Year of the point figure. Example: 2020.
        region: Geographical region for index value. Example: "pks" for \
                Pääkaupunkiseutu / Greater Helsinki area
        comment: Comment for the point figure. Example: "* preliminary data\r\n"
    """

    index = models.ForeignKey(
        OldDwellingsInHousingCompaniesPriceIndex,
        verbose_name=_("Index"),
        on_delete=models.PROTECT,
        related_name="point_figures",
    )
    # max_digits is arbitrary for the value. No need to limit it, although 7
    # should be enough if the values are at most in the 100s of thousands.
    # Largest point figure value in the system at the moment is year 1914's index
    # with a value around 260 000.
    value = models.DecimalField(
        verbose_name=_("Value"),
        decimal_places=1,
        max_digits=8,
        null=True,
    )
    year = models.PositiveSmallIntegerField(verbose_name=_("Year"))

    # Max lengths here are arbitrary, but set to avoid extra large input.
    region = models.CharField(verbose_name=_("Region"), blank=True, max_length=255)
    comment = models.TextField(verbose_name=_("Comment"), blank=True)

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Index point figure, yearly")
        verbose_name_plural = pgettext_lazy("Model name", "Index point figures, yearly")
        constraints = [
            models.UniqueConstraint(
                fields=["index", "year"], name="unique_price_index_point_figure"
            )
        ]
        ordering = ("-index", "-year")


class LeaseBasisOfRent(ArchivableModel, TimeStampedSafeDeleteModel):
    """
    In Finnish: Vuokranperusteet
    """

    lease = models.ForeignKey(
        "leasing.Lease",
        verbose_name=_("Lease"),
        related_name="basis_of_rents",
        on_delete=models.PROTECT,
    )

    # In Finnish: Tyyppi
    type = EnumField(
        BasisOfRentType,
        verbose_name=_("Type"),
        max_length=20,
        default=BasisOfRentType.LEASE,
    )

    parent = models.ForeignKey(
        "self",
        verbose_name=_("Lease basis of rent"),
        null=True,
        blank=True,
        related_name="children",
        on_delete=models.CASCADE,
    )

    # In Finnish: Käyttötarkoitus
    intended_use = models.ForeignKey(
        RentIntendedUse,
        verbose_name=_("Intended use"),
        related_name="+",
        on_delete=models.PROTECT,
    )

    # In Finnish: Pinta-ala
    area = models.DecimalField(
        verbose_name=_("Area amount"), decimal_places=2, max_digits=12
    )

    # In Finnish: Vyöhyke
    zone = EnumField(
        BasisOfRentZone, verbose_name=_("Zone"), null=True, blank=True, max_length=20
    )

    # In Finnish: Yksikkö
    area_unit = EnumField(AreaUnit, verbose_name=_("Area unit"), max_length=20)

    # In Finnish: Yksikköhinta (ind 100)
    amount_per_area = models.DecimalField(
        verbose_name=_("Amount per area (index 100)"),
        null=True,
        blank=True,
        max_digits=10,
        decimal_places=2,
    )

    # In Finnish: Indeksi
    index = models.ForeignKey(
        Index,
        verbose_name=_("Index"),
        related_name="+",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )

    # In Finnish: Tuottoprosentti
    profit_margin_percentage = models.DecimalField(
        verbose_name=_("Profit margin percentage"),
        null=True,
        blank=True,
        max_digits=10,
        decimal_places=2,
    )

    # In Finnish: Alennusprosentti
    discount_percentage = models.DecimalField(
        verbose_name=_("Discount percentage"),
        null=True,
        blank=True,
        max_digits=10,
        decimal_places=6,
    )

    # In Finnish: Piirustukset tarkastettu (Päivämäärä)
    plans_inspected_at = models.DateTimeField(
        verbose_name=_("Plans inspected at"), null=True, blank=True
    )

    # In Finnish: Piirustukset tarkastettu (Käyttäjä)
    plans_inspected_by = models.ForeignKey(
        User,
        verbose_name=_("Plans inspected by"),
        related_name="+",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )

    # In Finnish: Lukittu (Päivämäärä)
    locked_at = models.DateTimeField(verbose_name=_("Locked at"), null=True, blank=True)

    # In Finnish: Lukittu (Käyttäjä)
    locked_by = models.ForeignKey(
        User,
        verbose_name=_("Locked by"),
        related_name="+",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )

    # In Finnish: Subvention tyyppi
    subvention_type = EnumField(
        SubventionType,
        verbose_name=_("Subvention type"),
        null=True,
        blank=True,
        max_length=30,
    )

    # In Finnish: Markkinavuokran subventio
    subvention_base_percent = models.DecimalField(
        verbose_name=_("Subvention base percent"),
        null=True,
        blank=True,
        max_digits=10,
        decimal_places=2,
    )

    # In Finnish: Siirtymäajan subventio
    subvention_graduated_percent = models.DecimalField(
        verbose_name=_("Subvention graduated percent"),
        null=True,
        blank=True,
        max_digits=10,
        decimal_places=2,
    )

    recursive_get_related_skip_relations = ["lease"]

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Lease basis of rent")
        verbose_name_plural = pgettext_lazy("Model name", "Lease basis of rents")

    def delete(self, *args, **kwargs):
        # Skip delete if locked
        if self.locked_at is None:
            super().delete(*args, **kwargs)

    def get_index_adjusted_amount_per_area(self):
        """
        For new indexes (lease 2022), the amount per area is already adjusted.
        For old indexes, the amount per area needs to be adjusted by index number.
        """
        if self.type == BasisOfRentType.LEASE2022:
            return self.amount_per_area

        if self.amount_per_area is None:
            return Decimal(0)

        index_ratio = Decimal(1)
        if self.index:
            index_ratio = Decimal(self.index.number / 100)

        return self.amount_per_area * index_ratio

    def get_re_lease_subvention_percent(self):
        subvention_base_percent = (
            self.subvention_base_percent
            if self.subvention_base_percent is not None
            else 0
        )
        subvention_graduated_percent = (
            self.subvention_graduated_percent
            if self.subvention_graduated_percent is not None
            else 0
        )
        percent = (
            1
            - Decimal(1 - subvention_base_percent / 100)
            * Decimal(1 - subvention_graduated_percent / 100)
        ) * 100
        return percent

    def calculate_initial_year_rent(self):
        if (
            not self.area
            or not self.amount_per_area
            or not self.profit_margin_percentage
        ):
            return Decimal(0)

        initial_year_rent = (
            self.area * self.amount_per_area * self.profit_margin_percentage / 100
        )

        if self.index and self.type != BasisOfRentType.LEASE2022:
            initial_year_rent *= Decimal(self.index.number / 100)

        return initial_year_rent

    def calculate_subvented_initial_year_rent(self):
        initial_year_rent = self.calculate_initial_year_rent()

        if self.subvention_type == SubventionType.FORM_OF_MANAGEMENT:
            management_subventions = self.management_subventions.all()
            if not management_subventions:
                return round(initial_year_rent, 2)

            total_subvention_amount = Decimal(0)
            for management_subvention in management_subventions:
                total_subvention_amount += management_subvention.subvention_amount

            amount_per_area = self.get_index_adjusted_amount_per_area()

            subvention_percent = round(
                (1 - (total_subvention_amount / amount_per_area)) * 100, 2
            )

            discount_multiplier = (100 - subvention_percent) / 100

            return round(initial_year_rent, 2) * discount_multiplier

        if self.subvention_type == SubventionType.RE_LEASE:
            subvention_percent = self.get_re_lease_subvention_percent()
            return initial_year_rent * (1 - subvention_percent / 100)

        return round(initial_year_rent, 2)

    def calculate_subvention_euros_per_year(self):
        """
        In Finnish: Subventio euroa / vuosi
        """
        return (
            self.calculate_initial_year_rent()
            - self.calculate_subvented_initial_year_rent()
        ).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)

    def calculate_subvention_percent(self):
        """
        In Finnish: Subventio prosentteina
        """
        if (
            self.calculate_initial_year_rent().compare(Decimal(0)) == 0
            or self.calculate_subvention_amount().compare(Decimal(0)) == 0
        ):
            return Decimal(0)
        return (
            (self.calculate_subvention_amount() / self.calculate_initial_year_rent())
            * 100
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def calculate_subvention_amount_per_area(self):
        """
        In Finnish: Subventoitu yksikköhinta
        """
        subvention_amount_per_area = Decimal(0)
        if self.subvention_type == SubventionType.FORM_OF_MANAGEMENT:
            management_subventions = self.management_subventions.all()
            if management_subventions:
                for management_subvention in management_subventions:
                    subvention_amount_per_area += (
                        management_subvention.subvention_amount
                    )
        elif self.subvention_type == SubventionType.RE_LEASE:
            index_adjusted_amount_per_area = self.get_index_adjusted_amount_per_area()
            base_percent = (
                self.subvention_base_percent if self.subvention_base_percent else 0
            )
            graduated_percent = (
                self.subvention_graduated_percent
                if self.subvention_graduated_percent
                else 0
            )
            subvention_percent = (
                1
                - Decimal(1 - base_percent / 100) * Decimal(1 - graduated_percent / 100)
            ) * 100
            subvention_amount_per_area = index_adjusted_amount_per_area * (
                1 - (subvention_percent / 100)
            )
        return subvention_amount_per_area.quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

    def calculate_temporary_subvention_data(
        self,
    ) -> dict[str, Decimal | list[TemporarySubventionItem]]:
        """
        Returns the data for temporary subventions of the lease_basis_of_rent,
        both individual subventions and the total amount.

        Each subvention_amount_euros_per_year is calculated cumulatively.
        The subvention_percent is taken from the amount of subvented_initial_year_rent
        minus all the temporary subvention amounts that have been applied before it.
        """
        temporary_subventions = self.temporary_subventions.all()
        if not temporary_subventions:
            return {
                "temporary_subventions": [],
                "total_amount_euros_per_year": Decimal(0),
            }

        temporary_subvention_items = []
        temporary_discount_amount_total = Decimal(0)

        current_discounted_amount = round(
            self.calculate_subvented_initial_year_rent(), 6
        )
        for temporary_subvention in temporary_subventions:
            last_total = current_discounted_amount
            current_discounted_amount = (
                current_discounted_amount
                * (100 - temporary_subvention.subvention_percent)
                / 100
            )
            temporary_subvention_items.append(
                {
                    "description": temporary_subvention.description,
                    "subvention_percent": temporary_subvention.subvention_percent,
                    "subvention_amount_euros_per_year": Decimal(
                        last_total - current_discounted_amount
                    ),
                }
            )
        for subvention in temporary_subvention_items:
            temporary_discount_amount_total += subvention[
                "subvention_amount_euros_per_year"
            ]

        return {
            "temporary_subventions": temporary_subvention_items,
            "total_amount_euros_per_year": temporary_discount_amount_total,
        }

    def calculate_temporary_subvention_percentage(
        self,
    ) -> Decimal:
        base = Decimal(1)
        temporary_subventions = self.temporary_subventions.all()
        if not temporary_subventions:
            return Decimal(0)

        for temporary_subvention in temporary_subventions:
            base *= (100 - temporary_subvention.subvention_percent) / 100

        return (1 - base) * 100

    def calculate_discounted_rent(self):
        initial_year_rent = self.calculate_initial_year_rent()
        if not self.discount_percentage:
            return initial_year_rent

        discounted_rent = initial_year_rent * (100 - self.discount_percentage) / 100

        return discounted_rent

    def calculate_subvention_amount(self):
        subvention_amount = Decimal(0)
        if not self.area or not self.amount_per_area:
            return Decimal(0)

        if self.subvention_type == SubventionType.FORM_OF_MANAGEMENT:
            management_subventions = self.management_subventions.all()
            if management_subventions:
                management_subvention_amount_total = Decimal(0)
                for management_subvention in management_subventions:
                    management_subvention_amount_total += (
                        management_subvention.subvention_amount
                    )

                amount_per_area = self.get_index_adjusted_amount_per_area()

                subvention_amount = self.area * (
                    amount_per_area - management_subvention_amount_total
                )
                if self.profit_margin_percentage:
                    subvention_amount *= self.profit_margin_percentage / 100
        elif self.subvention_type == SubventionType.RE_LEASE:
            initial_year_rent = self.calculate_initial_year_rent()
            base_percent = (
                self.subvention_base_percent if self.subvention_base_percent else 0
            )
            graduated_percent = (
                self.subvention_graduated_percent
                if self.subvention_graduated_percent
                else 0
            )
            subvention_percent = (
                1
                - Decimal(1 - base_percent / 100) * Decimal(1 - graduated_percent / 100)
            ) * 100
            subvention_amount = initial_year_rent * (subvention_percent / 100)

        return subvention_amount


class LeaseBasisOfRentManagementSubvention(models.Model):
    lease_basis_of_rent = models.ForeignKey(
        LeaseBasisOfRent,
        verbose_name=_("Lease basis of rent"),
        related_name="management_subventions",
        on_delete=models.CASCADE,
    )

    # In Finnish: Hallintamuoto
    management = models.ForeignKey(
        ManagementSubventionFormOfManagement,
        verbose_name=_("Form of management"),
        related_name="+",
        on_delete=models.PROTECT,
    )

    # In Finnish: Subventio markkinavuokrasta / vuosi
    subvention_amount = models.DecimalField(
        verbose_name=_("Subvention amount"), max_digits=10, decimal_places=2
    )

    recursive_get_related_skip_relations = ["lease_basis_of_rent"]

    class Meta:
        verbose_name = pgettext_lazy(
            "Model name", "Management subvention (Basis of rent)"
        )
        verbose_name_plural = pgettext_lazy(
            "Model name", "Management subventions (Basis of rent)"
        )


class LeaseBasisOfRentTemporarySubvention(models.Model):
    lease_basis_of_rent = models.ForeignKey(
        LeaseBasisOfRent,
        verbose_name=_("Lease basis of rent"),
        related_name="temporary_subventions",
        on_delete=models.CASCADE,
    )

    # In Finnish: Kuvaus
    description = models.CharField(
        verbose_name=_("Description"), null=True, blank=True, max_length=255
    )

    # In Finnish: Subventio markkinavuokrasta prosenttia / vuosi
    subvention_percent = models.DecimalField(
        verbose_name=_("Subvention percent"), max_digits=10, decimal_places=2
    )

    recursive_get_related_skip_relations = ["lease_basis_of_rent"]

    class Meta:
        verbose_name = pgettext_lazy(
            "Model name", "Temporary subvention (Basis of rent)"
        )
        verbose_name_plural = pgettext_lazy(
            "Model name", "Temporary subventions (Basis of rent)"
        )


auditlog.register(Rent)
auditlog.register(RentDueDate)
auditlog.register(FixedInitialYearRent)
auditlog.register(ContractRent)
auditlog.register(RentAdjustment)
auditlog.register(LeaseBasisOfRent)

field_permissions.register(
    Rent,
    exclude_fields=[
        "lease",
        "index_adjusted_rents",
        "payable_rents",
        "equalized_rents",
    ],
)
field_permissions.register(RentDueDate, exclude_fields=["rent"])
field_permissions.register(FixedInitialYearRent, exclude_fields=["rent"])
field_permissions.register(ContractRent, exclude_fields=["rent"])
field_permissions.register(RentAdjustment, exclude_fields=["rent"])
field_permissions.register(LeaseBasisOfRent, exclude_fields=["lease"])
