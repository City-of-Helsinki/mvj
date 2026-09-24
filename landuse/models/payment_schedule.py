from django.db import models

from landuse.models.agreement import LandUseAgreement
from landuse.models.contract import Contract
from landuse.models.invoice import InvoiceItemType
from landuse.models.party import AgreementParty
from utils.mixins import TimeStampedModel

# English interest calculation method.
# Leap years not considered.
INTEREST_CALCULATION_DAYS_IN_YEAR = 365


class PaymentScheduleItemType(models.TextChoices):
    """
    In Finnish: Maksusuunnitelman erän maksurivin tyyppi
    """

    LAND_USE_COMPENSATION = (
        InvoiceItemType.LAND_USE_COMPENSATION.value,
        InvoiceItemType.LAND_USE_COMPENSATION.label,
    )
    INCREASE = (InvoiceItemType.INCREASE.value, InvoiceItemType.INCREASE.label)
    INTEREST = (InvoiceItemType.INTEREST.value, InvoiceItemType.INTEREST.label)


class PaymentScheduleStatus(models.TextChoices):
    """
    In Finnish: Maksusuunnitelman tila
    """

    DRAFT = ("DRAFT", "Luonnos")
    PENDING_APPROVAL = ("PENDING_APPROVAL", "Odottaa hyväksyntää")
    APPROVED = ("APPROVED", "Hyväksytty")
    REJECTED = ("REJECTED", "Hylätty")


class PaymentSchedule(TimeStampedModel):
    """
    In Finnish: Maksusuunnitelma
    """

    # In Finnish: Maankäyttösopimus
    agreement = models.ForeignKey(
        LandUseAgreement,
        on_delete=models.CASCADE,
        related_name="payment_schedules",
    )

    # In Finnish: Laskunsaaja
    recipient_party = models.ForeignKey(
        AgreementParty,
        on_delete=models.PROTECT,
        related_name="payment_schedules",
    )

    # In Finnish: Sopimus
    contract = models.ForeignKey(
        Contract,
        on_delete=models.PROTECT,
        related_name="payment_schedules",
    )

    # In Finnish: Tila
    status = models.CharField(
        choices=PaymentScheduleStatus.choices,
        default=PaymentScheduleStatus.DRAFT,
    )

    # In Finnish: Hylkäyksen syy
    rejected_reason = models.TextField(blank=True)

    # In Finnish: Allekirjoituspäivämäärä
    signing_date = models.DateField(null=True, blank=True)

    # In Finnish: Korotusprosentti
    increase_percentage = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
    )

    # In Finnish: Peruskorko
    base_interest_rate = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
    )

    # In Finnish: Korkomarginaali
    interest_margin = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
    )

    @staticmethod
    def get_interest_calculation_days_in_year() -> int:
        """In Finnish: Päiviä vuodessa korkolaskennassa"""
        return INTEREST_CALCULATION_DAYS_IN_YEAR


class PaymentScheduleInstallment(TimeStampedModel):
    """
    In Finnish: Maksusuunnitelman erä
    """

    # In Finnish: Maksusuunnitelma
    payment_schedule = models.ForeignKey(
        PaymentSchedule,
        on_delete=models.CASCADE,
        related_name="installments",
    )

    # In Finnish: Erän järjestysnumero maksusuunnitelmassa
    installment_sequence_number = models.PositiveSmallIntegerField()

    # In Finnish: Erien lukumäärä yhteensä maksusuunnitelmassa
    installment_count_total = models.PositiveSmallIntegerField()

    # In Finnish: Eräpäivä
    due_date = models.DateField(null=True, blank=True)

    # In Finnish: Koron/korotuksen laskentajakson alkupäivä
    interest_calculation_period_start_date = models.DateField(null=True, blank=True)

    # In Finnish: Koron/korotuksen laskentajakson loppupäivä
    interest_calculation_period_end_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ("installment_sequence_number",)
        constraints = [
            models.UniqueConstraint(
                fields=("payment_schedule", "installment_sequence_number"),
                name="unique_payment_schedule_installment_number",
            )
        ]


class PaymentScheduleInstallmentItem(TimeStampedModel):
    """
    In Finnish: Maksusuunnitelman erän maksurivi
    """

    # In Finnish: Maksusuunnitelman erä
    installment = models.ForeignKey(
        PaymentScheduleInstallment,
        on_delete=models.CASCADE,
        related_name="items",
    )

    # In Finnish: Maksurivin tyyppi
    item_type = models.CharField(choices=PaymentScheduleItemType)

    # In Finnish: Selite
    description = models.TextField(blank=True)

    # In Finnish: Summa
    amount = models.DecimalField(max_digits=20, decimal_places=2)

    class Meta:
        # Compensation items should globally be listed first, before other kinds of items.
        ordering = (
            models.Case(
                models.When(
                    item_type=PaymentScheduleItemType.LAND_USE_COMPENSATION,
                    then=models.Value(0),
                ),
                default=models.Value(1),
                output_field=models.IntegerField(),
            ),
            # Tie broken by primary keys in case of conflicts to ensure consistent ordering.
            "pk",
        )
