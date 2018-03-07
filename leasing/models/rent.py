from django.db import models
from django.utils.translation import ugettext_lazy as _

from .mixins import NameModel


# Note that this class is used in 4 other classes (unlike many other similar classes)
class RentPurpose(NameModel):
    pass


class RentType(NameModel):
    pass


class RentPeriod(NameModel):
    pass


class RentIndexIDNumber(NameModel):
    pass


class RentBillingType(NameModel):
    pass


class RentBasicInfo(models.Model):
    """This is the basic info for rent.

    Name in Finnish: Vuokran perustiedot
    """

    # Name in Finnish: Vuokralaji
    rent_type = models.ForeignKey(RentType, verbose_name=_("Rent type"), on_delete=models.PROTECT)

    # Name in Finnish: Vuokrakausi
    rent_period = models.ForeignKey(RentPeriod, verbose_name=_("Rent period"), on_delete=models.PROTECT, null=True)

    # Name in Finnish: Indeksin tunnusnumero
    index_id_number = models.ForeignKey(RentIndexIDNumber, verbose_name=_("Index ID number"), on_delete=models.PROTECT,
                                        null=True)

    # Name in Finnish: Laskutusjako
    billing_type = models.ForeignKey(RentBillingType, verbose_name=_("Rent billing type"), on_delete=models.PROTECT,
                                     null=True, related_name="+")

    # Name in Finnish: Laskut kpl / vuodessa
    bill_amount = models.PositiveIntegerField(verbose_name=_("Bill amount"), null=True, blank=True)

    # Name in Finnish: Perusindeksi
    basic_index = models.PositiveIntegerField(verbose_name=_("Basic index"), null=True, blank=True)

    # Name in Finnish: Pyöristys
    basic_index_rounding = models.PositiveIntegerField(verbose_name=_("Basic index rounding"), null=True, blank=True)

    # Name in Finnish: X-luku
    x_value = models.PositiveIntegerField(verbose_name=_("X value"), null=True, blank=True)

    # Name in Finnish: Y-luku
    y_value = models.PositiveIntegerField(verbose_name=_("Y value"), null=True, blank=True)

    # Name in Finnish: Y-alkaen
    y_value_start = models.PositiveIntegerField(verbose_name=_("Y value start"), null=True, blank=True)

    # Name in Finnish: Tasaus alkupvm
    adjustment_start_date = models.DateField(verbose_name=_("Adjustment start date"), null=True)

    # Name in Finnish: Tasaus loppupvm
    adjustment_end_date = models.DateField(verbose_name=_("Adjustment end date"), null=True)

    # Name in Finnish: Kertakaikkinen vuokra and Kiinteä vuokra
    rent_amount = models.PositiveIntegerField(verbose_name=_("Rent amount"), null=True, blank=True)


class FidexInitialYearRent(models.Model):
    """Name in Finnish: Kiinteä alkuvuosivuokra"""
    # Name in Finnish: No translation
    bill_amount = models.DecimalField(verbose_name=_("Bill amount"), max_digits=10, decimal_places=2)

    # Name in Finnish: Vuokra
    rent = models.ForeignKey(RentBasicInfo, verbose_name=_("Rent"), on_delete=models.CASCADE)

    # Name in Finnish: Alkupvm
    start_date = models.DateField(verbose_name=_("Start date"), null=True)

    # Name in Finnish: Loppupvm
    end_date = models.DateField(verbose_name=_("End date"), null=True)


class DueDate(models.Model):
    text = models.CharField(verbose_name=_("text"), max_length=255)
    rent = models.ForeignKey(RentBasicInfo, verbose_name=_("Rent"), on_delete=models.PROTECT)


class RentPaymentType(NameModel):
    """How many times per year is this rent paid?"""
    times_per_year = models.PositiveSmallIntegerField(verbose_name=_("Times paid per year"))


class ContractRent(models.Model):
    """Name in Finnish: Sopimusvuokra"""

    # Name in Finnish: Sopimusvuokra
    contract_rent = models.DecimalField(verbose_name=_("Contract rent"), max_digits=10, decimal_places=2)

    # Name in Finnish: No translation
    contract_rent_payment_type = models.ForeignKey(RentPaymentType, verbose_name=_("Contract rent payment type"),
                                                   on_delete=models.PROTECT, related_name="+")

    # Name in Finnish: Käyttötarkoitus
    purpose = models.ForeignKey(RentPurpose, verbose_name=_("Usage purpose"), on_delete=models.PROTECT)

    # Name in Finnish: Vuokranlaskennan perusteena oleva vuokra
    basic_rent = models.DecimalField(verbose_name=_("Basic rent"), max_digits=10, decimal_places=2)

    # Name in Finnish: No translation
    basic_rent_payment_type = models.ForeignKey(RentPaymentType, verbose_name=_("Basic rent payment type"),
                                                on_delete=models.PROTECT, related_name="+")

    # Name in Finnish: Uusi perusvuosi vuokra
    new_basic_year_rent = models.CharField(verbose_name=_("New basic year rent"), max_length=255)

    # Name in Finnish: Voimassaoloaika
    start_date = models.DateField(verbose_name=_("Start date"), null=True)

    # Name in Finnish: Voimassaoloaika
    end_date = models.DateField(verbose_name=_("End date"), null=True)


class IndexAdjustedRent(models.Model):
    """Name in Finnish: Indeksitarkistettu vuokra"""
    # Name in Finnish: Ind. tark. vuokra (€)
    rent = models.DecimalField(verbose_name=_("Rent"), max_digits=10, decimal_places=2)

    # Name in Finnish: Käyttötarkoitus
    purpose = models.ForeignKey(RentPurpose, verbose_name=_("Usage purpose"), on_delete=models.PROTECT)

    # Name in Finnish: Voimassaoloaika
    start_date = models.DateField()

    # Name in Finnish: No translation
    end_date = models.DateField()

    # Name in Finnish: Laskentak.
    calculation_factor = models.DecimalField(verbose_name=_("Rent"), max_digits=10, decimal_places=2)


class RentDiscountType(NameModel):
    pass


class RentDiscountAmountType(NameModel):
    pass


class RentDiscountRule(NameModel):
    pass


class RentDiscount(models.Model):
    """Name in Finnish: Alennukset ja korotukset"""

    # Name in Finnish: Tyyppi
    discount_type = models.ForeignKey(RentDiscountType, verbose_name=_("Discount type"), on_delete=models.PROTECT)

    # Name in Finnish: Käyttötarkoitus
    purpose = models.ForeignKey(RentPurpose, verbose_name=_("Usage purpose"), on_delete=models.PROTECT)

    # Name in Finnish: Alkupvm
    start_date = models.DateField(verbose_name=_("Start date"), null=True)

    # Name in Finnish: Loppupvm
    end_date = models.DateField(verbose_name=_("End date"), null=True)

    # Name in Finnish: Kokonaismäärä
    amount = models.PositiveIntegerField(verbose_name=_("Discount amount"), null=True, blank=True)

    # Name in Finnish: No translation
    amount_type = models.ForeignKey(RentDiscountAmountType, verbose_name=_("Discount type"), on_delete=models.PROTECT)

    # Name in Finnish: Jäljellä (€)
    amount_left = models.PositiveIntegerField(verbose_name=_("Discount amount"), null=True, blank=True)

    # Name in Finnish: Päätös
    rule = models.ForeignKey(RentDiscountRule, verbose_name=_("Discount rule"), on_delete=models.PROTECT)


class RentChargedRent(models.Model):
    """Name in Finnish: Perittävä vuokra"""

    # Name in Finnish: Perittävä vuokra (€)
    rent = models.DecimalField(verbose_name=_("Rent"), max_digits=10, decimal_places=2)

    # Name in Finnish: Voimassaoloaika
    start_date = models.DateField(verbose_name=_("Start date"), null=True)

    # Name in Finnish: No translation
    end_date = models.DateField(verbose_name=_("End date"), null=True)

    # Name in Finnish: Nousu %
    difference = models.DecimalField(verbose_name=_("Difference"), max_digits=5, decimal_places=2)

    # Name in Finnish: Kalenterivuosivuokra
    calendar_year_rent = models.DecimalField(verbose_name=_("Calendar year rent"), max_digits=10, decimal_places=2)


class RentCriteria(models.Model):
    """Name in Finnish: Vuokranperusteet"""

    # Name in Finnish: Käyttötarkoitus
    purpose = models.ForeignKey(RentPurpose, verbose_name=_("Usage purpose"), on_delete=models.PROTECT)

    # Name in Finnish: K-m2
    km2 = models.DecimalField(verbose_name=_("km2"), max_digits=10, decimal_places=2)

    # Name in Finnish: Indeksi
    index = models.DecimalField(verbose_name=_("Index"), max_digits=10, decimal_places=2)

    # Name in Finnish: € / k-m2 (ind 100)
    ekm2ind100 = models.DecimalField(verbose_name=_("emk2ind100"), max_digits=10, decimal_places=2)

    # Name in Finnish: € / k-m2 (ind)
    ekm2ind = models.DecimalField(verbose_name=_("emk2ind"), max_digits=10, decimal_places=2)

    # Name in Finnish: Prosenttia
    percentage = models.DecimalField(verbose_name=_("Percentage"), max_digits=10, decimal_places=2)

    # Name in Finnish: Perusvuosivuokra €/v (ind 100)
    basic_rent = models.DecimalField(verbose_name=_("Basic rent"), max_digits=10, decimal_places=2)

    # Name in Finnish: Perusvuosivuokra €/v (ind)
    starting_rent = models.DecimalField(verbose_name=_("Starting rent"), max_digits=10, decimal_places=2)


class Rent(models.Model):
    """Rent is paid by tenants for a lease.

    Name in Finnish: Vuokra
    """

    # Name in Finnish: Vuokran perustiedot
    basic_info = models.ForeignKey(RentBasicInfo, verbose_name=_("Rent"), on_delete=models.PROTECT)

    # Name in Finnish: Sopimusvuokra
    contract_rent = models.ForeignKey(ContractRent, verbose_name=_("Contract rent"), on_delete=models.PROTECT)

    # Name in Finnish: Indeksitarkistettu vuokra
    index_adjusted_rent = models.ForeignKey(IndexAdjustedRent, verbose_name=_("Index checked rent"),
                                            on_delete=models.PROTECT, related_name="parent")

    # Name in Finnish: Alennukset ja korotukset
    rent_discount = models.ForeignKey(RentDiscount, verbose_name=_("Adjustment"), on_delete=models.PROTECT)

    # Name in Finnish: Perittävä vuokra
    charged_rents = models.ForeignKey(RentChargedRent, verbose_name=_("Rent"), on_delete=models.PROTECT,
                                      related_name="parent")

    # Name in Finnish: Vuokran perusteet
    criterias = models.ForeignKey(RentCriteria, verbose_name=_("Rent"), on_delete=models.PROTECT)
