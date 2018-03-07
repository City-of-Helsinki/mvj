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

    Attributes:
        rent_type (ForeignKey): What type of rent is this.
            Name in Finnish: Vuokralaji
        rent_period (ForeignKey): What is the rent period.
            Name in Finnish: Vuokrakausi
        index_id_number (ForeignKey): Index ID number.
            Name in Finnish: Indeksin tunnusnumero
        billing_type (ForeignKey): Rent billing type.
            Name in Finnish: Laskutusjako
        bill_amount (PositiveIntegerField): Amount of bills per year.
            Name in Finnish: Laskut kpl / vuodessa
        bill_index (PositiveIntegerField): Index that is used.
            Name in Finnish: Perusindeksi
        basic_index_rounding (PositiveIntegerField):
            Name in Finnish: Pyöristys
        x_value (PositiveIntegerField):
            Name in Finnish: X-luku
        y_value (PositiveIntegerField):
            Name in Finnish: Y-luku
        y_value_start (PositiveIntegerField):
            Name in Finnish: Y-alkaen
        adjustment_start_date (DateField):
            Name in Finnish: Tasaus alkupvm
        adjustment_end_date (DateField):
            Name in Finnish: Tasaus loppupvm
        rent_amount (PositiveIntegerField):
            Name in Finnish: Kertakaikkinen vuokra and Kiinteä vuokra
    """

    rent_type = models.ForeignKey(
        RentType,
        verbose_name=_("Rent type"),
        on_delete=models.PROTECT,
    )

    rent_period = models.ForeignKey(
        RentPeriod,
        verbose_name=_("Rent period"),
        on_delete=models.PROTECT,
        null=True,
    )

    index_id_number = models.ForeignKey(
        RentIndexIDNumber,
        verbose_name=_("Index ID number"),
        on_delete=models.PROTECT,
        null=True,
    )

    billing_type = models.ForeignKey(
        RentBillingType,
        verbose_name=_("Rent billing type"),
        on_delete=models.PROTECT,
        null=True,
        related_name="+",
    )

    bill_amount = models.PositiveIntegerField(
        verbose_name=_("Bill amount"),
        null=True,
        blank=True,
    )

    basic_index = models.PositiveIntegerField(
        verbose_name=_("Basic index"),
        null=True,
        blank=True,
    )

    basic_index_rounding = models.PositiveIntegerField(
        verbose_name=_("Basic index rounding"),
        null=True,
        blank=True,
    )

    x_value = models.PositiveIntegerField(
        verbose_name=_("X value"),
        null=True,
        blank=True,
    )

    y_value = models.PositiveIntegerField(
        verbose_name=_("Y value"),
        null=True,
        blank=True,
    )

    y_value_start = models.PositiveIntegerField(
        verbose_name=_("Y value start"),
        null=True,
        blank=True,
    )

    adjustment_start_date = models.DateField(
        verbose_name=_("Adjustment start date"),
        null=True,
    )

    adjustment_end_date = models.DateField(
        verbose_name=_("Adjustment end date"),
        null=True,
    )

    rent_amount = models.PositiveIntegerField(
        verbose_name=_("Rent amount"),
        null=True,
        blank=True,
    )


class FidexInitialYearRent(models.Model):
    """Name in Finnish: Kiinteä alkuvuosivuokra

    Attributes:
        bill_amount (PositiveIntegerField):
            Name in Finnish: No translation
        rent (ForeignKey):
            Name in Finnish: Vuokra
        start_date (DateField):
            Name in Finnish: Alkupvm
        end_date (DateField):
            Name in Finnish: Loppupvm
    """
    bill_amount = models.DecimalField(
        verbose_name=_("Bill amount"),
        max_digits=10,
        decimal_places=2,
    )

    rent = models.ForeignKey(
        RentBasicInfo,
        verbose_name=_("Rent"),
        on_delete=models.CASCADE,
    )

    start_date = models.DateField(
        verbose_name=_("Start date"),
        null=True,
    )

    end_date = models.DateField(
        verbose_name=_("End date"),
        null=True,
    )


class DueDate(models.Model):
    text = models.CharField(
        verbose_name=_("text"),
        max_length=255,
    )

    rent = models.ForeignKey(
        RentBasicInfo,
        verbose_name=_("Rent"),
        on_delete=models.PROTECT,
    )


class RentPaymentType(NameModel):
    """How many times per year is this rent paid?"""
    times_per_year = models.PositiveSmallIntegerField(
        verbose_name=_("Times paid per year"),
    )


class ContractRent(models.Model):
    """Contract based rent.

    Name in Finnish: Sopimusvuokra
    Attributes:
        contract_rent (DecimalField): The amount of rent.
            Name in Finnish: Sopimusvuokra
        contract_rent_payment_type (ForeignKey):
            Name in Finnish: No translation
        purpose (ForeignKey):
            Name in Finnish: Käyttötarkoitus
        basic_rent (DecimalField):
            Name in Finnish: Vuokranlaskennan perusteena oleva vuokra
        basic_rent_payment_type:
            Name in Finnish: No translation
        new_basic_year_rent (CharField):
            Name in Finnish: Uusi perusvuosi vuokra
        start_date (DateField):
            Name in Finnish: Voimassaoloaika
        end_date (DateField):
            Name in Finnish: Voimassaoloaika
    """

    contract_rent = models.DecimalField(
        verbose_name=_("Contract rent"),
        max_digits=10,
        decimal_places=2,
    )

    contract_rent_payment_type = models.ForeignKey(
        RentPaymentType,
        verbose_name=_("Contract rent payment type"),
        on_delete=models.PROTECT,
        related_name="+",
    )

    purpose = models.ForeignKey(
        RentPurpose,
        verbose_name=_("Usage purpose"),
        on_delete=models.PROTECT,
    )

    basic_rent = models.DecimalField(
        verbose_name=_("Basic rent"),
        max_digits=10,
        decimal_places=2,
    )

    basic_rent_payment_type = models.ForeignKey(
        RentPaymentType,
        verbose_name=_("Basic rent payment type"),
        on_delete=models.PROTECT,
        related_name="+",
    )

    new_basic_year_rent = models.CharField(
        verbose_name=_("New basic year rent"),
        max_length=255,
    )

    start_date = models.DateField(
        verbose_name=_("Start date"),
        null=True,
    )

    end_date = models.DateField(
        verbose_name=_("End date"),
        null=True,
    )


class IndexAdjustedRent(models.Model):
    """
    Name in Finnish: Indeksitarkistettu vuokra

    Attributes:
        rent (DecimalField):
            Name in Finnish: Ind. tark. vuokra (€)
        purpose (ForeignKey):
            Name in Finnish: Käyttötarkoitus
        start_date (DateField):
            Name in Finnish: Voimassaoloaika
        end_date (DateField):
            Name in Finnish: No translation
        calculation_factor (DecimalField):
            Name in Finnish: Laskentak.
    """
    rent = models.DecimalField(
        verbose_name=_("Rent"),
        max_digits=10,
        decimal_places=2,
    )

    purpose = models.ForeignKey(
        RentPurpose,
        verbose_name=_("Usage purpose"),
        on_delete=models.PROTECT,
    )

    start_date = models.DateField()
    end_date = models.DateField()
    calculation_factor = models.DecimalField(
        verbose_name=_("Rent"),
        max_digits=10,
        decimal_places=2,
    )


class RentDiscountType(NameModel):
    pass


class RentDiscountAmountType(NameModel):
    pass


class RentDiscountRule(NameModel):
    pass


class RentDiscount(models.Model):
    """
    Name in Finnish: Alennukset ja korotukset

    Attributes
    discount_type (ForeignKey):
        Name in Finnish: Tyyppi
    purpose (ForeignKey):
        Name in Finnish: Käyttötarkoitus
    start_date (DateField):
        Name in Finnish: Alkupvm
    end_date (DateField):
        Name in Finnish: Loppupvm
    amount (PositiveIntegerField):
        Name in Finnish: Kokonaismäärä
    amount_type (ForeignKey):
        Name in Finnish: No translation
    amount_left (PositiveIntegerField):
        Name in Finnish: Jäljellä (€)
    rule (ForeignKey):
        Name in Finnish: Päätös
    """

    discount_type = models.ForeignKey(
        RentDiscountType,
        verbose_name=_("Discount type"),
        on_delete=models.PROTECT,
    )

    purpose = models.ForeignKey(
        RentPurpose,
        verbose_name=_("Usage purpose"),
        on_delete=models.PROTECT,
    )

    start_date = models.DateField(
        verbose_name=_("Start date"),
        null=True,
    )

    end_date = models.DateField(
        verbose_name=_("End date"),
        null=True,
    )

    amount = models.PositiveIntegerField(
        verbose_name=_("Discount amount"),
        null=True,
        blank=True,
    )

    amount_type = models.ForeignKey(
        RentDiscountAmountType,
        verbose_name=_("Discount type"),
        on_delete=models.PROTECT,
    )

    amount_left = models.PositiveIntegerField(
        verbose_name=_("Discount amount"),
        null=True,
        blank=True,
    )

    rule = models.ForeignKey(
        RentDiscountRule,
        verbose_name=_("Discount rule"),
        on_delete=models.PROTECT,
    )


class RentChargedRent(models.Model):
    """

    Name in Finnish: Perittävä vuokra

    Attributes:
        rent (DecimalField):
            Name in Finnish: Perittävä vuokra (€)
        start_date (DateField):
            Name in Finnish: Voimassaoloaika
        end_date (DateField):
            Name in Finnish: No translation
        difference (CharField):
            Name in Finnish: Nousu %
        calendar_year_rent (CharField):
            Name in Finnish: Kalenterivuosivuokra
    """

    rent = models.DecimalField(
        verbose_name=_("Rent"),
        max_digits=10,
        decimal_places=2,
    )

    start_date = models.DateField(
        verbose_name=_("Start date"),
        null=True,
    )

    end_date = models.DateField(
        verbose_name=_("End date"),
        null=True,
    )

    difference = models.DecimalField(
        verbose_name=_("Difference"),
        max_digits=5,
        decimal_places=2,
    )

    calendar_year_rent = models.DecimalField(
        verbose_name=_("Calendar year rent"),
        max_digits=10,
        decimal_places=2,
    )


class RentCriteria(models.Model):
    """
    Name in Finnish: Vuokranperusteet

    Attributes:
        purpose (ForeignKey):
            Name in Finnish: Käyttötarkoitus
        km2 (DecimalField):
            Name in Finnish: K-m2
        index (DecimalField):
            Name in Finnish: Indeksi
        ekm2ind100 (DecimalField):
            Name in Finnish: € / k-m2 (ind 100)
        ekm2ind (DecimalField):
            Name in Finnish: € / k-m2 (ind)
        percentage (DecimalField):
            Name in Finnish: Prosenttia
        basic_rent (DecimalField):
            Name in Finnish: Perusvuosivuokra €/v (ind 100)
        start_rent (DecimalField):
            Name in Finnish: Perusvuosivuokra €/v (ind)
    """

    purpose = models.ForeignKey(
        RentPurpose,
        verbose_name=_("Usage purpose"),
        on_delete=models.PROTECT,
    )

    km2 = models.DecimalField(
        verbose_name=_("km2"),
        max_digits=10,
        decimal_places=2,
    )

    index = models.DecimalField(
        verbose_name=_("Index"),
        max_digits=10,
        decimal_places=2,
    )

    ekm2ind100 = models.DecimalField(
        verbose_name=_("emk2ind100"),
        max_digits=10,
        decimal_places=2,
    )

    ekm2ind = models.DecimalField(
        verbose_name=_("emk2ind"),
        max_digits=10,
        decimal_places=2,
    )

    percentage = models.DecimalField(
        verbose_name=_("Percentage"),
        max_digits=10,
        decimal_places=2,
    )

    basic_rent = models.DecimalField(
        verbose_name=_("Basic rent"),
        max_digits=10,
        decimal_places=2,
    )

    starting_rent = models.DecimalField(
        verbose_name=_("Starting rent"),
        max_digits=10,
        decimal_places=2,
    )


class Rent(models.Model):
    """Rent is paid by tenants for a lease.

    Name in Finnish: Vuokra

    """
    basic_info = models.ForeignKey(
        RentBasicInfo,
        verbose_name=_("Rent"),
        on_delete=models.PROTECT,
    )

    contract_rent = models.ForeignKey(
        ContractRent,
        verbose_name=_("Rent"),
        on_delete=models.PROTECT,
    )

    index_adjusted_rent = models.ForeignKey(
        IndexAdjustedRent,
        verbose_name=_("Index checked rent"),
        on_delete=models.PROTECT,
        related_name="parent",
    )

    rent_discount = models.ForeignKey(
        RentDiscount,
        verbose_name=_("Adjustment"),
        on_delete=models.PROTECT,
    )

    charged_rents = models.ForeignKey(
        RentChargedRent,
        verbose_name=_("Rent"),
        on_delete=models.PROTECT,
        related_name="parent",
    )

    criterias = models.ForeignKey(
        RentCriteria,
        verbose_name=_("Rent"),
        on_delete=models.PROTECT,
    )
