from datetime import date
from decimal import Decimal

from auditlog.registry import auditlog
from dateutil.relativedelta import relativedelta
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from enumfields import EnumField

from leasing.enums import (
    DueDatesType, IndexType, PeriodType, RentAdjustmentAmountType, RentAdjustmentType, RentCycle, RentType)
from leasing.models.utils import (
    calculate_index_adjusted_value, get_date_range_amount_from_monthly_amount, get_range_overlap)

from .decision import Decision
from .mixins import NameModel, TimeStampedSafeDeleteModel


class RentIntendedUse(NameModel):
    """
    In Finnish: Käyttötarkoitus
    """


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

    def get_amount_for_year(self, year):
        date_range_start = date(year, 1, 1)
        date_range_end = date(year, 12, 31)
        return self.get_amount_for_date_range(date_range_start, date_range_end)

    def get_amount_for_month(self, year, month):
        date_range_start = date(year, month, 1)
        date_range_end = date(year, month, 1) + relativedelta(day=31)
        return self.get_amount_for_date_range(date_range_start, date_range_end)

    def get_amount_for_date_range(self, date_range_start, date_range_end):
        assert date_range_start <= date_range_end, 'date_range_start cannot be after date_range_end.'

        if self.type == RentType.INDEX and date_range_start.year != date_range_end.year:
            raise NotImplementedError('Cannot calculate index adjusted rent that is spanning multiple years.')

        range_filtering = Q(
            Q(Q(end_date=None) | Q(end_date__gte=date_range_start)) &
            Q(Q(start_date=None) | Q(start_date__lte=date_range_end)))

        fixed_initial_year_rents = self.fixed_initial_year_rents.filter(range_filtering)
        contract_rents = self.contract_rents.filter(range_filtering)
        rent_adjustments = self.rent_adjustments.filter(range_filtering)

        total = Decimal('0.00')

        for fixed_initial_year_rent in fixed_initial_year_rents:
            overlap = get_range_overlap(date_range_start, date_range_end, *fixed_initial_year_rent.date_range)
            rent_amount = fixed_initial_year_rent.get_amount_for_date_range(*overlap)
            total += rent_amount

        for contract_rent in contract_rents:
            overlap = get_range_overlap(date_range_start, date_range_end, *contract_rent.date_range)

            if not overlap:
                continue

            if self.type == RentType.FIXED:
                rent_amount = contract_rent.get_amount_for_date_range(*overlap)
            elif self.type == RentType.INDEX:
                original_rent_amount = contract_rent.get_amount_for_date_range(*overlap)
                rent_amount = self.get_index_adjusted_amount(date_range_start.year, original_rent_amount)
            else:
                raise NotImplementedError('Cannot calculate rent amount for rent type {}.'.format(self.type))

            adjust_amount = 0

            for rent_adjustment in rent_adjustments:
                if rent_adjustment.intended_use != contract_rent.intended_use:
                    continue

                overlap = get_range_overlap(date_range_start, date_range_end, *rent_adjustment.date_range)

                if not overlap:
                    continue

                adjust_amount += rent_adjustment.get_amount_for_date_range(rent_amount, *overlap)

            rent_amount = max(Decimal(0), rent_amount + adjust_amount)
            total += rent_amount

        return total

    @staticmethod
    def get_index_adjusted_amount(year, original_rent, index_type=IndexType.TYPE_7):
        index = Index.objects.get(year=year-1, month=None)
        return calculate_index_adjusted_value(original_rent, index, index_type)


class RentDueDate(TimeStampedSafeDeleteModel):
    """
    In Finnish: Eräpäivä
    """
    rent = models.ForeignKey(Rent, verbose_name=_("Rent"), related_name="due_dates", on_delete=models.CASCADE)
    day = models.IntegerField(verbose_name=_("Day"), validators=[MinValueValidator(1), MaxValueValidator(31)])
    month = models.IntegerField(verbose_name=_("Month"), validators=[MinValueValidator(1), MaxValueValidator(12)])


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

    @property
    def date_range(self):
        return self.start_date, self.end_date

    def get_amount_for_date_range(self, date_range_start, date_range_end):
        # TODO Implement this
        return Decimal('0.00')


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
    base_amount = models.DecimalField(verbose_name=_("Base amount"), max_digits=10, decimal_places=2)

    # In Finnish: Yksikkö
    base_amount_period = EnumField(PeriodType, verbose_name=_("Base amount period"), max_length=30)

    # In Finnish: Uusi perusvuosi vuokra
    base_year_rent = models.DecimalField(verbose_name=_("Base year rent"), null=True, blank=True, max_digits=10,
                                         decimal_places=2)

    # In Finnish: Alkupvm
    start_date = models.DateField(verbose_name=_("Start date"), null=True, blank=True)

    # In Finnish: Loppupvm
    end_date = models.DateField(verbose_name=_("End date"), null=True, blank=True)

    @property
    def date_range(self):
        return self.start_date, self.end_date

    def get_monthly_base_amount(self):
        if self.period == PeriodType.PER_MONTH:
            return self.base_amount
        elif self.period == PeriodType.PER_YEAR:
            return self.base_amount / 12
        else:
            raise NotImplementedError('Cannot calculate monthly rent for PeriodType {}'.format(self.period))

    def get_amount_for_date_range(self, date_range_start, date_range_end):
        if self.start_date:
            date_range_start = max(self.start_date, date_range_start)
        if self.end_date:
            date_range_end = min(self.end_date, date_range_end)

        if date_range_start > date_range_end:
            return Decimal('0.00')

        monthly_amount = self.get_monthly_base_amount()
        date_range_amount = get_date_range_amount_from_monthly_amount(monthly_amount, date_range_start, date_range_end)

        return date_range_amount


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


class Index(models.Model):
    """
    In Finnish: Indeksi
    """
    # In Finnish: Pisteluku
    number = models.PositiveIntegerField(verbose_name=_("Number"))

    year = models.PositiveSmallIntegerField(verbose_name=_("Year"))
    month = models.PositiveSmallIntegerField(verbose_name=_("Month"), null=True, blank=True,
                                             validators=[MinValueValidator(1), MaxValueValidator(12)])

    class Meta:
        verbose_name = _("Index")
        verbose_name_plural = _("Indexes")
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
