from django.contrib.postgres.fields import ArrayField
from django.db import models

from users.models import User
from utils.mixins import TimeStampedModel


class LandUseAgreementStatus(models.TextChoices):
    DRAFT = ("DRAFT", "Luonnos")
    IN_PROGRESS = ("IN_PROGRESS", "Vireillä")
    NEGOTIATION = ("NEGOTIATION", "Neuvottelu")
    DECISION = ("DECISION", "Päätös")
    SIGNATURE = ("SIGNATURE", "Allekirjoitus")
    NO_AGREEMENT = ("NO_AGREEMENT", "Ei sopimusta")


class DetailedPlanProcessingStage(models.TextChoices):
    DRAFT = ("DRAFT", "Vireillä")
    EFFECTIVE = ("EFFECTIVE", "Lainvoimainen")
    REVOKED = ("REVOKED", "Kumottu")


class District(TimeStampedModel):
    """
    In Finnish: Kaupunginosa
    """

    # In Finnish: Kaupunginosan nimi
    name = models.CharField(blank=False)

    # In Finnish: Kaupunginosan tunniste
    identifier = models.CharField(blank=False)

    class Meta:
        ordering = ("name",)


class AuthorizedSignatory(TimeStampedModel):
    """
    In Finnish: Toimivaltainen päättäjä
    """

    # In Finnish: Päättäjän nimi
    name = models.CharField(blank=False)


class LandUseAgreement(TimeStampedModel):
    """
    In Finnish: Maankäyttösopimus
    """

    # In Finnish: Maankäyttösopimuksen tunniste
    identifier = models.CharField(unique=True)

    # In Finnish: Kaupunginosa
    district = models.ForeignKey(
        District,
        on_delete=models.PROTECT,
        related_name="land_use_agreements",
        null=True,
    )

    # In Finnish: Edistämisalue
    is_promotion_area = models.BooleanField(default=False)

    # In Finnish: Maankäyttösopimuksen tila
    status = models.CharField(
        blank=True,
        choices=LandUseAgreementStatus,
        max_length=255,
    )

    # In Finnish: Arvioitu esittelyvuosi
    estimated_presentation_year = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
    )

    # In Finnish: Arvioitu maksuvuosi
    estimated_payment_year = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
    )

    # In Finnish: Sisältää asumismuotovelvoitteita (AM-velvoitteita)
    includes_housing_obligations = models.BooleanField(default=False)

    # In Finnish: Velvoitteiden määräaika
    obligations_deadline = models.DateField(null=True, blank=True)

    # In Finnish: Toimivaltainen päättäjä
    authorized_signatory = models.ForeignKey(
        AuthorizedSignatory,
        on_delete=models.PROTECT,
        related_name="land_use_agreements",
        null=True,
    )

    # In Finnish: Asemakaava
    detailed_plan = models.ForeignKey(
        "DetailedPlan",
        on_delete=models.PROTECT,
        related_name="land_use_agreements",
        null=True,
        blank=True,
    )

    # In Finnish: Kaava-alueen kohteet
    detailed_plan_sites = ArrayField(
        models.CharField(blank=True),
        blank=True,
        default=list,
    )

    # In Finnish: Vakuustarpeen korotuskerroin
    collateral_multiplier = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True,
    )

    class Meta:
        permissions = [
            ("view_tab_parties", "Can view parties tab"),
            ("change_tab_parties", "Can change parties tab"),
            ("view_tab_sites", "Can view sites tab"),
            ("change_tab_sites", "Can change sites tab"),
            ("view_tab_compensation", "Can view compensation tab"),
            ("change_tab_compensation", "Can change compensation tab"),
            ("view_tab_decisions", "Can view decisions tab"),
            ("change_tab_decisions", "Can change decisions tab"),
            ("view_tab_contracts", "Can view contracts tab"),
            ("change_tab_contracts", "Can change contracts tab"),
            ("view_tab_payment_schedules", "Can view payment schedules tab"),
            ("change_tab_payment_schedules", "Can change payment schedules tab"),
            ("view_tab_invoices", "Can view invoices tab"),
            ("change_tab_invoices", "Can change invoices tab"),
        ]


class AgreementAddress(TimeStampedModel):
    """
    In Finnish: Maankäyttösopimuksen osoite
    """

    # In Finnish: Maankäyttösopimus
    agreement = models.ForeignKey(
        LandUseAgreement,
        on_delete=models.CASCADE,
        related_name="addresses",
    )

    # In Finnish: Katuosoite
    street_address = models.CharField()

    # In Finnish: Postinumero
    postal_code = models.CharField()

    # In Finnish: Kaupunki
    city = models.CharField()


class AgreementPreparer(TimeStampedModel):
    """
    In Finnish: Maankäyttösopimuksen valmistelija
    """

    # In Finnish: Maankäyttösopimus
    agreement = models.ForeignKey(
        LandUseAgreement,
        on_delete=models.CASCADE,
        related_name="preparers",
    )

    # In Finnish: Valmistelija
    preparer = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="agreement_preparers"
    )


class DetailedPlan(TimeStampedModel):
    """
    In Finnish: Asemakaava
    """

    # In Finnish: Asemakaavan numero
    plan_number = models.CharField(unique=True)

    # In Finnish: Asemakaavan käsittelyvaihe
    processing_stage = models.CharField(
        blank=True,
        choices=DetailedPlanProcessingStage,
        max_length=255,
    )

    # In Finnish: Vahvistamis/hyväksymispäivä
    approval_date = models.DateField(null=True, blank=True)

    # In Finnish: Lainvoimaisuuspäivä
    effective_date = models.DateField(null=True, blank=True)

    # In Finnish: Asemakaavan hyväksyjä
    approver = models.CharField(blank=True)

    # In Finnish: Asemakaavan diaarinumero
    diary_number = models.CharField(blank=True)
