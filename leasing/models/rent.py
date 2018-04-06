from auditlog.registry import auditlog
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import ugettext_lazy as _
from enumfields import EnumField

from leasing.enums import (
    DueDatesType, IndexType, PeriodType, RentAdjustmentAmountType, RentAdjustmentType, RentCycle, RentType)

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

    # In Finnish: Kertakaikkinen vuokra and Kiinteä vuokra
    amount = models.DecimalField(verbose_name=_("Amount"), null=True, blank=True, max_digits=10, decimal_places=2)

    # In Finnish: Kommentti
    note = models.TextField(verbose_name=_("Note"), null=True, blank=True)

    is_active = models.BooleanField(verbose_name=_("Active?"), default=True)


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

    # In Finnish: Alkupvm
    start_date = models.DateField(verbose_name=_("Start date"), null=True, blank=True)

    # In Finnish: Loppupvm
    end_date = models.DateField(verbose_name=_("End date"), null=True, blank=True)


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


auditlog.register(Rent)
auditlog.register(RentDueDate)
auditlog.register(FixedInitialYearRent)
auditlog.register(ContractRent)
auditlog.register(RentAdjustment)
auditlog.register(LeaseBasisOfRent)
