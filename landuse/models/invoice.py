from decimal import Decimal
from typing import TYPE_CHECKING

from django.db import models, transaction
from django.db.models import Sum

from landuse.models.agreement import LandUseAgreement
from landuse.models.party import (
    AgreementParty,
    BillingDetails,
    BillingDetailsBase,
    PartyDetailsBase,
)
from utils.mixins import TimeStampedModel


class InvoiceType(models.TextChoices):
    LAND_USE_COMPENSATION = ("LAND_USE_COMPENSATION", "Maankäyttökorvaus")
    PENALTY = ("PENALTY", "Sakko")


class InvoiceStatus(models.TextChoices):
    DRAFT = ("DRAFT", "Luonnos")
    OPEN = ("OPEN", "Avoin")
    PAID = ("PAID", "Maksettu")
    CREDITED = ("CREDITED", "Hyvitetty")


class InvoiceItemType(models.TextChoices):
    LAND_USE_COMPENSATION = (
        "LAND_USE_COMPENSATION",
        "Maankäyttökorvaus",
    )
    INCREASE = ("INCREASE", "Korotus")
    INTEREST = ("INTEREST", "Korko")
    PENALTY = ("PENALTY", "Sakko")


class Invoice(TimeStampedModel):
    """
    In Finnish: Lasku
    """

    # In Finnish: Maankäyttösopimus
    agreement = models.ForeignKey(
        LandUseAgreement,
        on_delete=models.PROTECT,
        related_name="invoices",
    )

    # Connects an approved preview invoice to the actual invoice created from it.
    source_payment_schedule_installment = models.OneToOneField(
        "landuse.PaymentScheduleInstallment",
        on_delete=models.PROTECT,
        related_name="invoice",
        null=True,
        blank=True,
    )

    # In Finnish: Laskunsaajaosapuoli
    recipient_party = models.ForeignKey(
        AgreementParty,
        on_delete=models.PROTECT,
        related_name="invoices",
    )

    # In Finnish: Erän järjestysnumero laskusarjassa
    installment_sequence_number = models.PositiveSmallIntegerField()

    # In Finnish: Erien lukumäärä yhteensä laskusarjassa
    installment_count_total = models.PositiveSmallIntegerField()

    # In Finnish: Eräpäivä
    due_date = models.DateField(null=True, blank=True)

    # In Finnish: Laskun tunniste
    invoice_identifier = models.CharField(blank=True, unique=True)

    # In Finnish: Laskun tyyppi
    invoice_type = models.CharField(choices=InvoiceType, blank=True)

    # In Finnish: Laskun tila
    status = models.CharField(
        choices=InvoiceStatus,
        default=InvoiceStatus.DRAFT,
    )

    # In Finnish: Lähetetty SAP:iin
    sent_at = models.DateTimeField(null=True, blank=True)

    # In Finnish: Laskutettu summa
    billed_amount = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        null=True,
        blank=True,
    )

    if TYPE_CHECKING:
        payments: models.Manager["ShadowSalesLedgerEntry"]

    @transaction.atomic
    def save(self, *args, **kwargs):
        create_recipient_snapshot = self._state.adding

        if (
            self.installment_count_total
            and self.installment_sequence_number
            and self.installment_sequence_number > self.installment_count_total
        ):
            raise ValueError(
                "Installment sequence number cannot be greater than the total installment count."
            )

        super().save(*args, **kwargs)

        if create_recipient_snapshot:
            InvoiceRecipientSnapshot.create_for_invoice(self)

    def get_remaining_amount(self) -> Decimal | None:
        """How much is left unpaid on this invoice."""
        if self.billed_amount is None:
            return None

        paid_amount = self.payments.aggregate(total=Sum("paid_amount"))["total"]
        return self.billed_amount - (paid_amount or Decimal("0"))


class InvoiceRecipientSnapshot(PartyDetailsBase, BillingDetailsBase):
    """Recipient and billing details as they were when the invoice was created."""

    invoice = models.OneToOneField(
        Invoice,
        on_delete=models.CASCADE,
        related_name="recipient_snapshot",
    )

    @classmethod
    def create_for_invoice(cls, invoice: Invoice) -> "InvoiceRecipientSnapshot":
        recipient = invoice.recipient_party.get_primary_invoice_recipient()
        snapshot_fields = (
            PartyDetailsBase._meta.get_fields() + BillingDetailsBase._meta.get_fields()
        )
        snapshot_values = {
            field_name: getattr(recipient, field_name) for field_name in snapshot_fields
        }

        try:
            billing_details: BillingDetails | None = (
                invoice.recipient_party.billing_details
            )
            snapshot_values.update(
                ovt_code=billing_details.ovt_code,
                sap_customer_number=billing_details.sap_customer_number,
                customer_reference=billing_details.customer_reference,
            )
        except BillingDetails.DoesNotExist:
            # Currently the BillingDetails model contains only optional fields.
            pass

        return cls.objects.create(invoice=invoice, **snapshot_values)


class InvoiceItem(TimeStampedModel):
    """
    In Finnish: Laskurivi
    """

    # In Finnish: Lasku
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name="items",
    )

    # In Finnish: Laskurivin tyyppi
    item_type = models.CharField(choices=InvoiceItemType)

    # In Finnish: Selite
    description = models.TextField(blank=True)

    # In Finnish: Summa
    amount = models.DecimalField(max_digits=20, decimal_places=2)

    class Meta:
        # Compensation items should globally be listed first, before other kinds of items.
        ordering = (
            models.Case(
                models.When(
                    item_type=InvoiceItemType.LAND_USE_COMPENSATION,
                    then=models.Value(0),
                ),
                default=models.Value(1),
                output_field=models.IntegerField(),
            ),
            # Tie broken by primary keys in case of conflicts to ensure consistent ordering.
            "pk",
        )


class ShadowSalesLedgerEntry(TimeStampedModel):
    """
    A payment reported by the master ledger system (SAP) for an invoice.

    In Finnish: Varjoreskontran maksusuoritus
    """

    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name="payments",
    )

    # In Finnish: Maksettu määrä
    paid_amount = models.DecimalField(max_digits=20, decimal_places=2)

    # In Finnish: Maksettu päivämäärällä
    paid_date = models.DateField()

    # In Finnish: Arkistointitunnus
    filing_code = models.CharField(max_length=35, blank=True)
