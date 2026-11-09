from typing import Any

from django.contrib.postgres.fields import ArrayField
from django.db import models

from landuse.models.agreement import LandUseAgreement
from landuse.models.decision import Decision
from landuse.models.party import AgreementParty


class ContractDetailsBase(models.Model):
    """
    Shared properties for contracts and contract changes.
    """

    # In Finnish: Sopimusnumero
    contract_number = models.CharField(blank=True)

    # In Finnish: Allekirjoituspäivämäärä
    signing_date = models.DateField(null=True, blank=True)

    # In Finnish: Allekirjoitettava mennessä
    signing_deadline = models.DateField(null=True, blank=True)

    # In Finnish: 1. kutsu lähetetty
    first_call_sent = models.DateField(null=True, blank=True)

    # In Finnish: 2. kutsu lähetetty
    second_call_sent = models.DateField(null=True, blank=True)

    # In Finnish: 3. kutsu lähetetty
    third_call_sent = models.DateField(null=True, blank=True)

    # In Finnish: Toimeenpanija
    executor = models.CharField(null=True, blank=True)

    # In Finnish: Päätös
    decision = models.ForeignKey(
        Decision,
        on_delete=models.CASCADE,
        related_name="%(class)s_contract_schedule_details",
        null=True,
        blank=True,
    )

    class Meta:
        abstract = True


class Contract(ContractDetailsBase):
    """
    In Finnish: Sopimus
    """

    class ContractType(models.TextChoices):
        LAND_USE_AGREEMENT = ("land_use_agreement", "Maankäyttösopimus")
        REAL_ESTATE_PRELIMINARY_AGREEMENT = (
            "real_estate_preliminary_agreement",
            "Kiinteistökaupan esitietosopimus",
        )
        OTHER = ("other", "Muu")

    # In Finnish: Maankäyttösopimus
    agreement = models.ForeignKey(
        LandUseAgreement,
        on_delete=models.CASCADE,
        related_name="contracts",
    )

    # In Finnish: Otsikko
    title = models.CharField(blank=True)

    # In Finnish: Sopimuksen tyyppi
    contract_type = models.CharField(
        choices=ContractType.choices,
        blank=True,
    )

    # In Finnish: Huomautus
    signing_note = models.TextField(blank=True)


class ContractChange(ContractDetailsBase):
    """
    In Finnish: Sopimuksen muutos
    """

    # In Finnish: Sopimus
    contract = models.ForeignKey(
        Contract,
        on_delete=models.CASCADE,
        related_name="contract_changes",
    )

    # In Finnish: Selite
    description = models.TextField(blank=True)


class CollateralBase(models.Model):
    """
    Shared fields for all collateral types.
    """

    class CollateralType(models.TextChoices):
        MORTGAGE_DOCUMENT = ("mortgage_document", "Panttikirja")
        FINANCIAL_GUARANTEE = ("financial_guarantee", "Rahavakuus")
        SELF_DEBTOR_GUARANTEE = ("self_debtor_guarantee", "Omavelkainen takaus")
        PLEDGE_OF_FUNDS = ("pledge_of_funds", "Tilivarojen panttaus")
        OTHER = ("other", "Muu vakuus")

    # In Finnish: Sopimus
    contract = models.ForeignKey(
        Contract,
        on_delete=models.CASCADE,
        related_name="%(class)s_collaterals",
    )

    # In Finnish: Vakuuden tyyppi
    collateral_type = models.CharField(choices=CollateralType.choices)

    # In Finnish: Osapuolet
    parties = models.ManyToManyField(
        AgreementParty,
        related_name="%(class)s_collaterals",
        blank=True,
    )

    # In Finnish: Vierasvelkapanttauksen antajan nimi
    third_party_pledgor_name = models.CharField(
        null=True,
        blank=True,
    )
    # In Finnish: Vierasvelkapanttauksen antajan y-tunnus
    third_party_pledgor_business_id = models.CharField(null=True, blank=True)

    # In Finnish: Alkupäivämäärä
    start_date = models.DateField(null=True, blank=True)

    # In Finnish: Päättymispäivämäärä
    end_date = models.DateField(null=True, blank=True)

    # In Finnish: Määrä (€)
    amount = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        null=True,
        blank=True,
    )

    # In Finnish: Palautettu päivämäärällä
    returned_date = models.DateField(null=True, blank=True)

    # In Finnish: Palautuksen merkitsijä
    marked_returned_by = models.CharField(null=True, blank=True)

    # In Finnish: Lisätiedot
    additional_information = models.TextField(blank=True)

    class Meta:
        abstract = True

    def save(self, *args: Any, **kwargs: Any) -> None:
        if any([self.returned_date, self.marked_returned_by]) and not all(
            [self.returned_date, self.marked_returned_by]
        ):
            raise ValueError(
                "Both returned date and marked returned by must be set together."
            )

        super().save(*args, **kwargs)

    def is_third_party_pledge(self) -> bool:
        """
        In Finnish: Onko kyseessä vierasvelkapanttaus?
        """
        return bool(
            self.third_party_pledgor_name or self.third_party_pledgor_business_id
        )


class CollateralDocumentDetailsBase(models.Model):
    """
    Shared document fields for documented collateral types.
    """

    class DocumentCategory(models.TextChoices):
        ELECTRONIC = ("electronic", "Sähköinen")
        PAPER = ("paper", "Paperinen")

    # In Finnish: Vakuusasiakirjan laji
    document_type = models.CharField(
        choices=DocumentCategory,
        blank=True,
    )

    class Meta:
        abstract = True


class GuarantorDetailsBase(models.Model):
    """
    Shared guarantor fields for collateral types that require them.
    """

    # In Finnish: Vakuuden antajan nimi
    pledgor_name = models.CharField(blank=True)

    # In Finnish: Vakuuden antajan Y-tunnus
    pledgor_business_id = models.CharField(blank=True)

    # In Finnish: Vakuuden antajan henkilötunnus
    pledgor_national_identification_number = models.CharField(blank=True)

    class Meta:
        abstract = True


class MortgageDeedCollateral(CollateralBase, CollateralDocumentDetailsBase):
    """
    In Finnish: Panttikirja
    """

    class CollateralTarget(models.TextChoices):
        PROPERTY = ("property", "Kiinteistö")
        FACILITY = ("facility", "Laitos")

    # In Finnish: Kohde (Kiinteistö vai laitos)
    target = models.CharField(
        choices=CollateralTarget.choices,
        blank=True,
    )

    # In Finnish: Laitostunnus
    institution_identifier = models.CharField(null=True, blank=True)

    # In Finnish: Panttikirjan numero
    mortgage_document_number = models.CharField()

    # In Finnish: Panttikirjan päiväys
    mortgage_deed_date = models.DateField()

    # In Finnish: Jälkipantin saajan nimi
    subordinate_pledgee_name = models.CharField(null=True, blank=True)

    # In Finnish: Jälkipantin saajan y-tunnus
    subordinate_pledgee_business_id = models.CharField(null=True, blank=True)

    # In Finnish: Panttikirjan kiinteistötunnukset
    property_identifiers = ArrayField(
        models.CharField(blank=True),
        default=list,
        blank=True,
    )

    def save(self, *args: Any, **kwargs: Any) -> None:
        if (
            self.target == MortgageDeedCollateral.CollateralTarget.PROPERTY
            and self.institution_identifier
        ):
            raise ValueError("Facility identifier cannot be set for property target.")
        if (
            self.target == MortgageDeedCollateral.CollateralTarget.FACILITY
            and not self.institution_identifier
        ):
            raise ValueError("Facility identifier must be set for facility target.")
        if (
            self.target == MortgageDeedCollateral.CollateralTarget.FACILITY
            and self.property_identifiers
        ):
            raise ValueError("Property identifier cannot be set for facility target.")

        super().save(*args, **kwargs)


class CashDepositCollateral(CollateralBase, GuarantorDetailsBase):
    """
    In Finnish: Rahavakuus
    """

    # In Finnish: Tilinumero
    account_number = models.CharField(blank=True)

    # In Finnish: Maksettu päivämäärällä
    paid_at_date = models.DateField(null=True, blank=True)


class PersonalGuaranteeCollateral(
    CollateralBase,
    CollateralDocumentDetailsBase,
    GuarantorDetailsBase,
):
    """
    In Finnish: Omavelkainen takaus
    """

    # In Finnish: Takausnumero
    guarantee_number = models.CharField(blank=True)


class DepositPledgeCollateral(
    CollateralBase,
    CollateralDocumentDetailsBase,
    GuarantorDetailsBase,
):
    """
    In Finnish: Tilivarojen panttaus
    """

    # In Finnish: Tilinumero
    account_number = models.CharField(blank=True)


class OtherCollateral(
    CollateralBase,
    CollateralDocumentDetailsBase,
    GuarantorDetailsBase,
):
    """
    In Finnish: Muu vakuus
    """

    # No additional fields besides those inherited from the base classes
    pass
