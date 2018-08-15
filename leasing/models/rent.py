import datetime
from decimal import Decimal

from auditlog.registry import auditlog
from dateutil.relativedelta import relativedelta
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils.translation import pgettext_lazy
from django.utils.translation import ugettext_lazy as _
from enumfields import EnumField

from leasing.enums import (
    DueDatesPosition, DueDatesType, IndexType, PeriodType, RentAdjustmentAmountType, RentAdjustmentType, RentCycle,
    RentType)
from leasing.models.utils import (
    DayMonth, Explanation, IndexCalculation, fix_amount_for_overlap, get_billing_periods_for_year,
    get_date_range_amount_from_monthly_amount, get_monthly_amount_by_period_type, get_range_overlap_and_remainder,
    split_date_range)

from .decision import Decision
from .mixins import NameModel, TimeStampedSafeDeleteModel

first_day_of_every_month = []

for i in range(1, 13):
    first_day_of_every_month.append(DayMonth(day=1, month=i))

FIXED_DUE_DATES = {
    DueDatesPosition.START_OF_MONTH: {
        1: [DayMonth(day=2, month=1)],
        2: [DayMonth(day=2, month=1), DayMonth(day=1, month=7)],
        4: [DayMonth(day=2, month=1), DayMonth(day=1, month=4), DayMonth(day=1, month=7), DayMonth(day=1, month=10)],
        12: first_day_of_every_month,
    },
    DueDatesPosition.MIDDLE_OF_MONTH: {
        1: [DayMonth(day=30, month=6)],
        2: [DayMonth(day=15, month=3), DayMonth(day=30, month=9)],
        4: [DayMonth(day=1, month=3), DayMonth(day=15, month=4), DayMonth(day=15, month=7), DayMonth(day=15, month=10)],
        12: first_day_of_every_month,
    }
}


class RentIntendedUse(NameModel):
    """
    In Finnish: Käyttötarkoitus
    """
    class Meta(NameModel.Meta):
        verbose_name = pgettext_lazy("Model name", "Rent intended use")
        verbose_name_plural = pgettext_lazy("Model name", "Rent intended uses")


class Rent(TimeStampedSafeDeleteModel):
    """
    In Finnish: Vuokran perustiedot
    """
    lease = models.ForeignKey('leasing.Lease', verbose_name=_("Lease"), related_name='rents',
                              on_delete=models.PROTECT)

    # In Finnish: Vuokralaji
    type = EnumField(RentType, verbose_name=_("Type"), max_length=30)

    # In Finnish: Vuokrakausi
    cycle = EnumField(RentCycle, verbose_name=_("Cycle"), null=True, blank=True, max_length=30)

    # In Finnish: Indeksin tunnusnumero
    index_type = EnumField(IndexType, verbose_name=_("Index type"), null=True, blank=True, max_length=30)

    # In Finnish: Laskutusjako
    due_dates_type = EnumField(DueDatesType, verbose_name=_("Due dates type"), null=True, blank=True, max_length=30)

    # In Finnish: Laskut kpl / vuodessa
    due_dates_per_year = models.PositiveIntegerField(verbose_name=_("Due dates per year"), null=True, blank=True)

    # In Finnish: Perusindeksi
    elementary_index = models.PositiveIntegerField(verbose_name=_("Elementary index"), null=True, blank=True)

    # In Finnish: Pyöristys
    index_rounding = models.PositiveIntegerField(verbose_name=_("Index rounding"), null=True, blank=True)

    # In Finnish: X-luku
    x_value = models.PositiveIntegerField(verbose_name=_("X value"), null=True, blank=True)

    # In Finnish: Y-luku
    y_value = models.PositiveIntegerField(verbose_name=_("Y value"), null=True, blank=True)

    # In Finnish: Y-alkaen
    y_value_start = models.PositiveIntegerField(verbose_name=_("Y value start"), null=True, blank=True)

    # In Finnish: Tasaus alkupvm
    equalization_start_date = models.DateField(verbose_name=_("Equalization start date"), null=True, blank=True)

    # In Finnish: Tasaus loppupvm
    equalization_end_date = models.DateField(verbose_name=_("Equalization end date"), null=True, blank=True)

    # In Finnish: Määrä (vain kun tyyppi on kertakaikkinen vuokra)
    amount = models.DecimalField(verbose_name=_("Amount"), null=True, blank=True, max_digits=10, decimal_places=2)

    # In Finnish: Kommentti
    note = models.TextField(verbose_name=_("Note"), null=True, blank=True)

    # In Finnish: Alkupvm
    start_date = models.DateField(verbose_name=_("Start date"), null=True, blank=True)

    # In Finnish: Loppupvm
    end_date = models.DateField(verbose_name=_("End date"), null=True, blank=True)

    # In Finnish: Kausilaskutus
    seasonal_start_day = models.PositiveIntegerField(verbose_name=_("Seasonal start day"), null=True, blank=True,
                                                     validators=[MinValueValidator(1), MaxValueValidator(31)])
    seasonal_start_month = models.PositiveIntegerField(verbose_name=_("Seasonal start month"), null=True, blank=True,
                                                       validators=[MinValueValidator(1), MaxValueValidator(12)])
    seasonal_end_day = models.PositiveIntegerField(verbose_name=_("Seasonal end day"), null=True, blank=True,
                                                   validators=[MinValueValidator(1), MaxValueValidator(31)])
    seasonal_end_month = models.PositiveIntegerField(verbose_name=_("Seasonal end month"), null=True, blank=True,
                                                     validators=[MinValueValidator(1), MaxValueValidator(12)])

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Rent")
        verbose_name_plural = pgettext_lazy("Model name", "Rents")

    def is_seasonal(self):
        return (self.seasonal_start_day and self.seasonal_start_month and
                self.seasonal_end_day and self.seasonal_end_month)

    def get_amount_for_year(self, year):
        date_range_start = datetime.date(year, 1, 1)
        date_range_end = datetime.date(year, 12, 31)
        return self.get_amount_for_date_range(date_range_start, date_range_end)

    def get_amount_for_month(self, year, month):
        date_range_start = datetime.date(year, month, 1)
        date_range_end = datetime.date(year, month, 1) + relativedelta(day=31)
        return self.get_amount_for_date_range(date_range_start, date_range_end)

    def get_amount_for_date_range(self, date_range_start, date_range_end, explain=False):  # noqa: C901 TODO
        assert date_range_start <= date_range_end, 'date_range_start cannot be after date_range_end.'

        if self.type == RentType.INDEX and date_range_start.year != date_range_end.year:
            raise NotImplementedError('Cannot calculate index adjusted rent that is spanning multiple years.')

        explanation = Explanation()

        range_filtering = Q(
            Q(Q(end_date=None) | Q(end_date__gte=date_range_start)) &
            Q(Q(start_date=None) | Q(start_date__lte=date_range_end)))

        fixed_initial_year_rents = self.fixed_initial_year_rents.filter(range_filtering)
        contract_rents = self.contract_rents.filter(range_filtering)
        rent_adjustments = self.rent_adjustments.filter(range_filtering)

        total = Decimal('0.00')
        fixed_applied = False
        remaining_ranges = []

        if self.is_seasonal():
            seasonal_period_start = datetime.date(year=date_range_start.year, month=self.seasonal_start_month,
                                                  day=self.seasonal_start_day)
            seasonal_period_end = datetime.date(year=date_range_start.year, month=self.seasonal_end_month,
                                                day=self.seasonal_end_day)

            if date_range_start < seasonal_period_start and date_range_start < seasonal_period_end:
                date_range_start = seasonal_period_start

            if date_range_end > seasonal_period_end and date_range_end > seasonal_period_start:
                date_range_end = seasonal_period_end

        for fixed_initial_year_rent in fixed_initial_year_rents:
            (fixed_overlap, fixed_remainders) = get_range_overlap_and_remainder(
                date_range_start, date_range_end, *fixed_initial_year_rent.date_range)

            if not fixed_overlap:
                continue

            if fixed_remainders:
                remaining_ranges.extend(fixed_remainders)

            fixed_applied = True

            fixed_amount = fixed_initial_year_rent.get_amount_for_date_range(*fixed_overlap)

            fixed_explanation_item = explanation.add(
                subject=fixed_initial_year_rent, date_ranges=[fixed_overlap], amount=fixed_amount)

            for rent_adjustment in rent_adjustments:
                if fixed_initial_year_rent.intended_use and \
                        rent_adjustment.intended_use != fixed_initial_year_rent.intended_use:
                    continue

                (adjustment_overlap, adjustment_remainders) = get_range_overlap_and_remainder(
                    fixed_overlap[0], fixed_overlap[1], *rent_adjustment.date_range)

                if not adjustment_overlap:
                    continue

                tmp_amount = fix_amount_for_overlap(fixed_amount, adjustment_overlap, adjustment_remainders)
                adjustment_amount = rent_adjustment.get_amount_for_date_range(tmp_amount, *adjustment_overlap)
                fixed_amount += adjustment_amount

                explanation.add(subject=rent_adjustment, date_ranges=[adjustment_overlap], amount=adjustment_amount,
                                related_item=fixed_explanation_item)

            total += fixed_amount

        if fixed_applied:
            if not remaining_ranges:
                if explain:
                    explanation.add(subject=self, date_ranges=[(date_range_start, date_range_end)], amount=total)

                    return total, explanation
                else:
                    return total
            else:
                date_ranges = remaining_ranges
        else:
            date_ranges = [(date_range_start, date_range_end)]

        for (range_start, range_end) in date_ranges:
            for contract_rent in contract_rents:
                (contract_overlap, _) = get_range_overlap_and_remainder(
                    range_start, range_end, *contract_rent.date_range)

                if not contract_overlap:
                    continue

                if self.type == RentType.FIXED:
                    contract_amount = contract_rent.get_amount_for_date_range(*contract_overlap)
                    contract_rent_explanation_item = explanation.add(
                        subject=contract_rent, date_ranges=[contract_overlap], amount=contract_amount)
                elif self.type == RentType.INDEX:
                    original_rent_amount = contract_rent.get_base_amount_for_date_range(*contract_overlap)

                    index = Index.objects.get_latest_for_date(contract_overlap[0])

                    index_calculation = IndexCalculation(amount=original_rent_amount, index=index,
                                                         index_type=self.index_type, precision=self.index_rounding,
                                                         x_value=self.x_value, y_value=self.y_value)

                    contract_amount = index_calculation.calculate()

                    contract_rent_explanation_item = explanation.add(
                        subject=contract_rent, date_ranges=[contract_overlap], amount=original_rent_amount)

                    index_explanation_item = explanation.add(subject=index, date_ranges=[contract_overlap],
                                                             amount=contract_amount,
                                                             related_item=contract_rent_explanation_item)

                    for item in index_calculation.explanation_items:
                        explanation.add_item(item, related_item=index_explanation_item)

                elif self.type in (RentType.FREE, RentType.MANUAL):
                    # TODO: MANUAL rent type
                    continue
                else:
                    raise NotImplementedError('RentType {} not implemented'.format(self.type))

                for rent_adjustment in rent_adjustments:
                    if rent_adjustment.intended_use != contract_rent.intended_use:
                        continue

                    (adjustment_overlap, adjustment_remainders) = get_range_overlap_and_remainder(
                        range_start, range_end, *rent_adjustment.date_range)

                    if not adjustment_overlap:
                        continue

                    tmp_amount = fix_amount_for_overlap(contract_amount, adjustment_overlap, adjustment_remainders)
                    adjustment_amount = rent_adjustment.get_amount_for_date_range(tmp_amount, *adjustment_overlap)
                    contract_amount += adjustment_amount

                    explanation.add(subject=rent_adjustment, date_ranges=[adjustment_overlap], amount=adjustment_amount,
                                    related_item=contract_rent_explanation_item)

                total += contract_amount

        explanation.add(subject=self, date_ranges=[(date_range_start, date_range_end)], amount=total)

        if explain:
            return total, explanation
        else:
            return total

    def get_custom_due_dates_as_daymonths(self):
        if self.due_dates_type != DueDatesType.CUSTOM:
            return set()

        return [dd.as_daymonth() for dd in self.due_dates.all().order_by('month', 'day')]

    def get_due_dates_as_daymonths(self):
        due_dates = []
        if self.due_dates_type == DueDatesType.FIXED:
            # TODO: handle unknown due date count
            if self.due_dates_per_year in (1, 2, 4, 12):
                due_dates = FIXED_DUE_DATES[self.lease.type.due_dates_position][self.due_dates_per_year]
        elif self.due_dates_type == DueDatesType.CUSTOM:
            due_dates = self.get_custom_due_dates_as_daymonths()

        return due_dates

    def get_due_dates_for_period(self, start_date, end_date):
        if (self.end_date and start_date > self.end_date) or (self.start_date and end_date < self.start_date):
            return []

        rent_due_dates = self.get_due_dates_as_daymonths()

        period_years = {start_date.year, end_date.year}
        due_dates = []
        for rent_due_date in rent_due_dates:
            for year in period_years:
                tmp_date = datetime.date(year=year, month=rent_due_date.month, day=rent_due_date.day)
                if tmp_date >= start_date and tmp_date <= end_date:
                    due_dates.append(tmp_date)

        return due_dates

    def get_billing_period_from_due_date(self, due_date):
        if not due_date:
            return None

        # Non-seasonal rent
        if not self.is_seasonal():
            due_dates_per_year = self.get_due_dates_for_period(datetime.date(year=due_date.year, month=1, day=1),
                                                               datetime.date(year=due_date.year, month=12, day=31))

            try:
                due_date_index = due_dates_per_year.index(due_date)

                return get_billing_periods_for_year(due_date.year, len(due_dates_per_year))[due_date_index]
            except (ValueError, IndexError):
                # TODO: better error handling
                return None

        # Seasonal rent
        seasonal_period_start = datetime.date(year=due_date.year, month=self.seasonal_start_month,
                                              day=self.seasonal_start_day)
        seasonal_period_end = datetime.date(year=due_date.year, month=self.seasonal_end_month,
                                            day=self.seasonal_end_day)

        if seasonal_period_start > due_date or seasonal_period_end < due_date:
            return None

        due_dates_in_period = self.get_due_dates_for_period(seasonal_period_start, seasonal_period_end)
        if not due_dates_in_period:
            return None
        elif len(due_dates_in_period) == 1 and due_dates_in_period[0] == due_date:
            return seasonal_period_start, seasonal_period_end
        else:
            try:
                due_date_index = due_dates_in_period.index(due_date)
            except ValueError:
                return None

            return split_date_range((seasonal_period_start, seasonal_period_end), len(due_dates_in_period))[
                due_date_index]


class RentDueDate(TimeStampedSafeDeleteModel):
    """
    In Finnish: Eräpäivä
    """
    rent = models.ForeignKey(Rent, verbose_name=_("Rent"), related_name="due_dates", on_delete=models.CASCADE)
    day = models.IntegerField(verbose_name=_("Day"), validators=[MinValueValidator(1), MaxValueValidator(31)])
    month = models.IntegerField(verbose_name=_("Month"), validators=[MinValueValidator(1), MaxValueValidator(12)])

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Rent due date")
        verbose_name_plural = pgettext_lazy("Model name", "Rent due dates")

    def as_daymonth(self):
        return DayMonth(day=self.day, month=self.month)


class FixedInitialYearRent(TimeStampedSafeDeleteModel):
    """
    In Finnish: Kiinteä alkuvuosivuokra
    """
    rent = models.ForeignKey(Rent, verbose_name=_("Rent"), related_name='fixed_initial_year_rents',
                             on_delete=models.CASCADE)

    # In Finnish: Vuokra
    amount = models.DecimalField(verbose_name=_("Amount"), max_digits=10, decimal_places=2)

    # In Finnish: Käyttötarkoitus
    intended_use = models.ForeignKey(RentIntendedUse, verbose_name=_("Intended use"), null=True, blank=True,
                                     on_delete=models.PROTECT)

    # In Finnish: Alkupvm
    start_date = models.DateField(verbose_name=_("Start date"), null=True, blank=True)

    # In Finnish: Loppupvm
    end_date = models.DateField(verbose_name=_("End date"), null=True, blank=True)

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
        date_range_amount = get_date_range_amount_from_monthly_amount(monthly_amount, date_range_start, date_range_end,
                                                                      real_month_lengths=False)

        return date_range_amount


class ContractRent(TimeStampedSafeDeleteModel):
    """
    In Finnish: Sopimusvuokra
    """
    rent = models.ForeignKey(Rent, verbose_name=_("Rent"), related_name='contract_rents', on_delete=models.CASCADE)

    # In Finnish: Sopimusvuokra
    amount = models.DecimalField(verbose_name=_("Amount"), max_digits=10, decimal_places=2)

    # In Finnish: Yksikkö
    period = EnumField(PeriodType, verbose_name=_("Period"), max_length=30)

    # In Finnish: Käyttötarkoitus
    intended_use = models.ForeignKey(RentIntendedUse, verbose_name=_("Intended use"), on_delete=models.PROTECT)

    # In Finnish: Vuokranlaskennan perusteena oleva vuokra
    base_amount = models.DecimalField(verbose_name=_("Base amount"), null=True, blank=True, max_digits=10,
                                      decimal_places=2)

    # In Finnish: Yksikkö
    base_amount_period = EnumField(PeriodType, verbose_name=_("Base amount period"), null=True, blank=True,
                                   max_length=30)

    # In Finnish: Uusi perusvuosi vuokra
    base_year_rent = models.DecimalField(verbose_name=_("Base year rent"), null=True, blank=True, max_digits=10,
                                         decimal_places=2)

    # In Finnish: Alkupvm
    start_date = models.DateField(verbose_name=_("Start date"), null=True, blank=True)

    # In Finnish: Loppupvm
    end_date = models.DateField(verbose_name=_("End date"), null=True, blank=True)

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
            return Decimal('0.00')

        if amount_type == "amount":
            monthly_amount = get_monthly_amount_by_period_type(self.amount, self.period)
        else:
            monthly_amount = get_monthly_amount_by_period_type(self.base_amount, self.base_amount_period)

        date_range_amount = get_date_range_amount_from_monthly_amount(monthly_amount, date_range_start, date_range_end)

        return date_range_amount

    def get_amount_for_date_range(self, date_range_start, date_range_end):
        return self._get_amount_for_date_range(date_range_start, date_range_end, "amount")

    def get_base_amount_for_date_range(self, date_range_start, date_range_end):
        return self._get_amount_for_date_range(date_range_start, date_range_end, "base_amount")


class IndexAdjustedRent(models.Model):
    """
    In Finnish: Indeksitarkistettu vuokra
    """
    rent = models.ForeignKey(Rent, verbose_name=_("Rent"), related_name='index_adjusted_rents',
                             on_delete=models.CASCADE)

    # In Finnish: Indeksitarkistettu vuokra
    amount = models.DecimalField(verbose_name=_("Amount"), max_digits=10, decimal_places=2)

    # In Finnish: Käyttötarkoitus
    intended_use = models.ForeignKey(RentIntendedUse, verbose_name=_("Intended use"), on_delete=models.PROTECT)

    # In Finnish: Alkupvm
    start_date = models.DateField(verbose_name=_("Start date"))

    # In Finnish: Loppupvm
    end_date = models.DateField(verbose_name=_("End date"))

    # In Finnish: Laskentak.
    factor = models.DecimalField(verbose_name=_("Factor"), max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Index adjusted rent")
        verbose_name_plural = pgettext_lazy("Model name", "Index adjusted rents")


class RentAdjustment(TimeStampedSafeDeleteModel):
    """
    In Finnish: Alennukset ja korotukset
    """
    rent = models.ForeignKey(Rent, verbose_name=_("Rent"), related_name='rent_adjustments', on_delete=models.CASCADE)

    # In Finnish: Tyyppi
    type = EnumField(RentAdjustmentType, verbose_name=_("Type"), max_length=30)

    # In Finnish: Käyttötarkoitus
    intended_use = models.ForeignKey(RentIntendedUse, verbose_name=_("Intended use"), on_delete=models.PROTECT)

    # In Finnish: Alkupvm
    start_date = models.DateField(verbose_name=_("Start date"), null=True, blank=True)

    # In Finnish: Loppupvm
    end_date = models.DateField(verbose_name=_("End date"), null=True, blank=True)

    # In Finnish: Kokonaismäärä
    full_amount = models.DecimalField(verbose_name=_("Full amount"), null=True, blank=True, max_digits=10,
                                      decimal_places=2)

    # In Finnish: Määrän tyyppi
    amount_type = EnumField(RentAdjustmentAmountType, verbose_name=_("Amount type"), max_length=30)

    # In Finnish: Jäljellä
    amount_left = models.DecimalField(verbose_name=_("Amount left"), null=True, blank=True, max_digits=10,
                                      decimal_places=2)

    # In Finnish: Päätös
    decision = models.ForeignKey(Decision, verbose_name=_("Decision"), null=True, blank=True, on_delete=models.PROTECT)

    # In Finnish: Kommentti
    note = models.TextField(verbose_name=_("Note"), null=True, blank=True)

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Rent adjustment")
        verbose_name_plural = pgettext_lazy("Model name", "Rent adjustments")

    @property
    def date_range(self):
        return self.start_date, self.end_date

    def get_amount_for_date_range(self, rent_amount, date_range_start, date_range_end):
        if self.start_date:
            date_range_start = max(self.start_date, date_range_start)
        if self.end_date:
            date_range_end = min(self.end_date, date_range_end)

        if date_range_start > date_range_end:
            return Decimal('0.00')

        if self.amount_type == RentAdjustmentAmountType.PERCENT_PER_YEAR:
            adjustment = self.full_amount / 100 * rent_amount
        elif self.amount_type == RentAdjustmentAmountType.AMOUNT_PER_YEAR:
            adjustment = get_date_range_amount_from_monthly_amount(self.full_amount / 12, date_range_start,
                                                                   date_range_end)
        elif self.amount_type == RentAdjustmentAmountType.AMOUNT_TOTAL:
            adjustment_left = self.amount_left

            if self.amount_left is None:
                adjustment_left = self.full_amount

            adjustment = min(adjustment_left, rent_amount)
            self.amount_left = max(0, adjustment_left - adjustment)
            # TODO: This is for demonstration only! The new amount_left should be saved only when the invoice is created
            self.save()
        else:
            raise NotImplementedError(
                'Cannot get adjust amount for RentAdjustmentAmountType {}'.format(self.amount_type))

        if self.type == RentAdjustmentType.INCREASE:
            return adjustment
        elif self.type == RentAdjustmentType.DISCOUNT:
            return -adjustment
        else:
            raise NotImplementedError(
                'Cannot get adjust amount for RentAdjustmentType {}'.format(self.amount_type))


class PayableRent(models.Model):
    """
    In Finnish: Perittävä vuokra
    """
    rent = models.ForeignKey(Rent, verbose_name=_("Rent"), related_name='payable_rents', on_delete=models.CASCADE)

    # In Finnish: Perittävä vuokra
    amount = models.DecimalField(verbose_name=_("Amount"), max_digits=10, decimal_places=2)

    # In Finnish: Alkupvm
    start_date = models.DateField(verbose_name=_("Start date"), null=True, blank=True)

    # In Finnish: Loppupvm
    end_date = models.DateField(verbose_name=_("End date"), null=True, blank=True)

    # In Finnish: Nousu %
    difference_percent = models.DecimalField(verbose_name=_("Difference percent"), max_digits=10, decimal_places=2)

    # In Finnish: Kalenterivuosivuokra
    calendar_year_rent = models.DecimalField(verbose_name=_("Calendar year rent"), max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Payable rent")
        verbose_name_plural = pgettext_lazy("Model name", "Payable rents")


class LeaseBasisOfRent(models.Model):
    """
    In Finnish: Vuokranperusteet
    """
    lease = models.ForeignKey('leasing.Lease', verbose_name=_("Lease"), related_name='basis_of_rents',
                              on_delete=models.PROTECT)

    # In Finnish: Käyttötarkoitus
    intended_use = models.ForeignKey(RentIntendedUse, verbose_name=_("Intended use"), on_delete=models.PROTECT)

    # In Finnish: K-m2
    floor_m2 = models.DecimalField(verbose_name=_("Floor m2"), null=True, blank=True, max_digits=10, decimal_places=2)

    # In Finnish: Indeksi
    index = models.PositiveIntegerField(verbose_name=_("Index"), null=True, blank=True)

    # In Finnish: € / k-m2 (ind 100)
    amount_per_floor_m2_index_100 = models.DecimalField(verbose_name=_("Amount per floor m^2 (index 100)"), null=True,
                                                        blank=True, max_digits=10, decimal_places=2)

    # In Finnish: € / k-m2 (ind)
    amount_per_floor_m2_index = models.DecimalField(verbose_name=_("Amount per floor m^2 (index)"), null=True,
                                                    blank=True, max_digits=10, decimal_places=2)

    # In Finnish: Prosenttia
    percent = models.DecimalField(verbose_name=_("Percent"), null=True, blank=True, max_digits=10,
                                  decimal_places=2)

    # In Finnish: Perusvuosivuokra €/v (ind 100)
    year_rent_index_100 = models.DecimalField(verbose_name=_("Year rent (index 100)"), null=True, blank=True,
                                              max_digits=10, decimal_places=2)

    # In Finnish: Perusvuosivuokra €/v (ind)
    year_rent_index = models.DecimalField(verbose_name=_("Year rent (index)"), null=True, blank=True, max_digits=10,
                                          decimal_places=2)

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Lease basis of rent")
        verbose_name_plural = pgettext_lazy("Model name", "Lease basis of rents")


class IndexManager(models.Manager):
    def get_latest_for_date(self, the_date=None):
        """Returns the previous years average index or the latest monthly index related to the date"""
        if the_date is None:
            the_date = datetime.date.today()

        try:
            return self.get_queryset().get(year=the_date.year - 1, month__isnull=True)
        except Index.DoesNotExist:
            pass

        return self.get_queryset().filter(
            Q(year=the_date.year, month__lte=the_date.month) | Q(year__lt=the_date.year)
        ).order_by('-year', '-month').first()


class Index(models.Model):
    """
    In Finnish: Indeksi
    """
    # In Finnish: Pisteluku
    number = models.PositiveIntegerField(verbose_name=_("Number"))

    year = models.PositiveSmallIntegerField(verbose_name=_("Year"))
    month = models.PositiveSmallIntegerField(verbose_name=_("Month"), null=True, blank=True,
                                             validators=[MinValueValidator(1), MaxValueValidator(12)])

    objects = IndexManager()

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Index")
        verbose_name_plural = pgettext_lazy("Model name", "Indexes")
        indexes = [
            models.Index(fields=["year", "month"]),
        ]
        unique_together = ("year", "month")
        ordering = ("year", "month")

    def __str__(self):
        return "{} {} {}".format(self.year, self.month, self.number)


auditlog.register(Rent)
auditlog.register(RentDueDate)
auditlog.register(FixedInitialYearRent)
auditlog.register(ContractRent)
auditlog.register(RentAdjustment)
auditlog.register(LeaseBasisOfRent)
