from django.db import models

from landuse.models.agreement import LandUseAgreement
from landuse.models.decision import Decision
from landuse.models.party import AgreementParty
from utils.mixins import TimeStampedModel


class ContractScheduleDetailsBase(models.Model):
    """
    Shared signing and invitation dates for contracts and contract changes.
    """

    # In Finnish: Allekirjoituspäivämäärä
    signing_date = models.DateField(null=True, blank=True)

    # In Finnish: Allekirjoitettava mennessä
    signing_deadline = models.DateField(null=True, blank=True)

    # In Finnish: 1. kutsu lähetetty
    first_invitation_sent_date = models.DateField(null=True, blank=True)

    # In Finnish: 2. kutsu lähetetty
    second_invitation_sent_date = models.DateField(null=True, blank=True)

    # In Finnish: 3. kutsu lähetetty
    third_invitation_sent_date = models.DateField(null=True, blank=True)

    # In Finnish: Päätös
    decision = models.ForeignKey(
        Decision,
        on_delete=models.CASCADE,
        related_name="contract_schedule_details",
        null=True,
        blank=True,
    )

    # In Finnish: Huomautus
    note = models.TextField(blank=True)

    class Meta:
        abstract = True


class Contract(ContractScheduleDetailsBase):
    """
    In Finnish: Sopimus
    """

    class ContractType(models.TextChoices):
        LAND_USE_AGREEMENT = ("LAND_USE_AGREEMENT", "Maankäyttösopimus")
        REAL_ESTATE_PRELIMINARY_AGREEMENT = (
            "REAL_ESTATE_PRELIMINARY_AGREEMENT",
            "Kiinteistökaupan esitietosopimus",
        )
        OTHER = ("OTHER", "Muu")

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

    # In Finnish: Sopimusnumero
    contract_number = models.CharField(blank=True)


class ContractChange(ContractScheduleDetailsBase):
    """
    In Finnish: Sopimuksen muutos
    """

    # In Finnish: Sopimus
    contract = models.ForeignKey(
        Contract,
        on_delete=models.CASCADE,
        related_name="changes",
    )


class CollateralBase(models.Model):
    """
    Shared fields for all collateral types.
    """

    class CollateralType(models.TextChoices):
        MORTGAGE_DEED = ("MORTGAGE_DEED", "Panttikirja")
        CASH_DEPOSIT = ("CASH_DEPOSIT", "Rahavakuus")
        PERSONAL_GUARANTEE = ("PERSONAL_GUARANTEE", "Omavelkainen takaus")
        DEPOSIT_PLEDGE = ("DEPOSIT_PLEDGE", "Tilivarojen panttaus")
        OTHER = ("OTHER", "Muu vakuus")

    # In Finnish: Sopimus
    contract = models.ForeignKey(
        Contract,
        on_delete=models.CASCADE,
        related_name="%(class)s_collaterals",
    )

    # In Finnish: Vakuuden tyyppi
    guarantee_type = models.CharField(choices=CollateralType.choices)

    # In Finnish: Osapuolet
    parties = models.ManyToManyField(
        AgreementParty,
        related_name="%(class)s_collaterals",
        blank=True,
    )

    # In Finnish: Vierasvelkapanttauksen antajan nimi
    third_party_pledger_name = models.CharField(
        null=True,
        blank=True,
    )
    # In Finnish: Vierasvelkapanttauksen antajan y-tunnus
    third_party_pledger_business_id = models.CharField(null=True, blank=True)

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

    # In Finnish: Lisätiedot
    additional_information = models.TextField(blank=True)

    class Meta:
        abstract = True

    def is_third_party_pledge(self) -> bool:
        """
        In Finnish: Onko kyseessä vierasvelkapanttaus?
        """
        return bool(
            self.third_party_pledger_name or self.third_party_pledger_business_id
        )


class CollateralDocumentDetailsBase(models.Model):
    """
    Shared document fields for documented collateral types.
    """

    class DocumentCategory(models.TextChoices):
        ELECTRONIC = ("ELECTRONIC", "Sähköinen")
        PAPER = ("PAPER", "Paperinen")

    # In Finnish: Vakuusasiakirjan laji
    document_category = models.CharField(
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
    guarantor_name = models.CharField(blank=True)

    # In Finnish: Vakuuden antajan Y-tunnus
    guarantor_business_id = models.CharField(blank=True)

    # In Finnish: Vakuuden antajan henkilötunnus
    guarantor_national_identification_number = models.CharField(blank=True)

    class Meta:
        abstract = True


class MortgageDeedCollateral(CollateralBase, CollateralDocumentDetailsBase):
    """
    In Finnish: Panttikirja
    """

    class CollateralTarget(models.TextChoices):
        PROPERTY = ("PROPERTY", "Kiinteistö")
        FACILITY = ("FACILITY", "Laitos")

    # In Finnish: Kohde (Kiinteistö vai laitos)
    target = models.CharField(
        choices=CollateralTarget.choices,
        blank=True,
    )

    # In Finnish: Laitostunnus
    facility_identifier = models.CharField(blank=True)

    # In Finnish: Panttikirjan numero
    mortgage_deed_number = models.CharField(blank=True)

    # In Finnish: Panttikirjan päiväys
    mortgage_deed_date = models.DateField(null=True, blank=True)


class MortgageDeedPropertyIdentifier(TimeStampedModel):
    """
    In Finnish: Panttikirjan kiinteistötunnus
    """

    # In Finnish: Panttikirja
    collateral = models.ForeignKey(
        MortgageDeedCollateral,
        on_delete=models.CASCADE,
        related_name="property_identifiers",
    )

    # In Finnish: Kiinteistötunnus
    identifier = models.CharField(blank=True)


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
    guarantee_identifier = models.CharField(blank=True)


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
