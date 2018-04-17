from auditlog.registry import auditlog
from django.db import models
from django.utils.translation import ugettext_lazy as _
from enumfields import EnumField

from leasing.enums import InvoiceDeliveryMethod, InvoiceStatus, InvoiceType
from leasing.models import Contact
from leasing.models.mixins import TimeStampedSafeDeleteModel


class ReceivableType(models.Model):
    """
    In Finnish: Saamislaji
    """
    name = models.CharField(verbose_name=_("Name"), max_length=255)
    sap_code = models.CharField(verbose_name=_("SAP code"), max_length=255)

    class Meta:
        verbose_name = _("Receivable type")
        verbose_name_plural = _("Receivable types")

    def __str__(self):
        return "{} {}".format(self.name, self.sap_code)


class Invoice(TimeStampedSafeDeleteModel):
    """
    In Finnish: Lasku
    """
    lease = models.ForeignKey('leasing.Lease', verbose_name=_("Lease"), related_name='invoices',
                              on_delete=models.PROTECT)

    # In Finnish: Laskunsaaja
    recipient = models.ForeignKey(Contact, verbose_name=_("Recipient"), on_delete=models.PROTECT)

    # In Finnish: Lähetetty SAP:iin
    sent_to_sap_at = models.DateTimeField(verbose_name=_("Sent to SAP at"), null=True, blank=True)

    # In Finnish: SAP numero
    sap_id = models.CharField(verbose_name=_("SAP ID"), max_length=255, blank=True)

    # In Finnish: Eräpäivä
    due_date = models.DateField(verbose_name=_("Due date"))

    # In Finnish: Laskutuspvm
    invoicing_date = models.DateField(verbose_name=_("Invoicing date"), null=True, blank=True)

    # In Finnish: Saamislaji
    receivable_type = models.ForeignKey(ReceivableType, verbose_name=_("Receivable type"), on_delete=models.PROTECT)

    # In Finnish: Laskun tila
    status = EnumField(InvoiceStatus, verbose_name=_("Status"))

    # In Finnish: Laskutuskauden alkupvm
    billing_period_start_date = models.DateField(verbose_name=_("Billing period start date"))

    # In Finnish: Laskutuskauden loppupvm
    billing_period_end_date = models.DateField(verbose_name=_("Billing period end date"))

    # In Finnish: Lykkäyspvm
    postpone_date = models.DateField(verbose_name=_("Postpone date"), null=True, blank=True)

    # In Finnish: Laskun pääoma
    rent_amount = models.DecimalField(verbose_name=_("Rent amount"), max_digits=10, decimal_places=2)

    # In Finnish: Laskun osuuden jaettava
    share_numerator = models.PositiveIntegerField(verbose_name=_("Share numerator"))

    # In Finnish: Laskun osuuden jakaja
    share_denominator = models.PositiveIntegerField(verbose_name=_("Share denominator"))

    # In Finnish: Laskutettu määrä
    billed_amount = models.DecimalField(verbose_name=_("Billed amount"), max_digits=10, decimal_places=2)

    # In Finnish: Maksettu määrä
    paid_amount = models.DecimalField(verbose_name=_("Paid amount"), null=True, blank=True, max_digits=10,
                                      decimal_places=2)

    # In Finnish Maksettu pvm
    paid_date = models.DateField(verbose_name=_("Paid date"), null=True, blank=True)

    # In Finnish: Maksamaton määrä
    outstanding_amount = models.DecimalField(verbose_name=_("Outstanding amount"), null=True, blank=True, max_digits=10,
                                             decimal_places=2)

    # In Finnish: Maksukehotuspvm
    payment_notification_date = models.DateField(verbose_name=_("Payment notification date"), null=True, blank=True)

    # In Finnish: Perintäkulu
    collection_charge = models.DecimalField(verbose_name=_("Collection charge"), null=True, blank=True, max_digits=10,
                                            decimal_places=2)

    # In Finnish: Maksukehotus luettelo
    payment_notification_catalog_date = models.DateField(verbose_name=_("Payment notification catalog date"), null=True,
                                                         blank=True)

    # In Finnish: E vai paperilasku
    delivery_method = EnumField(InvoiceDeliveryMethod, verbose_name=_("Delivery method"), null=True, blank=True)

    # In Finnish: Laskun tyyppi
    type = EnumField(InvoiceType, verbose_name=_("Type"))

    # In Finnish: Tiedote
    notes = models.TextField(verbose_name=_("Notes"), blank=True)

    class Meta:
        verbose_name = _("Invoice")
        verbose_name_plural = _("Invoices")

    def __str__(self):
        return str(self.pk)


class BankHoliday(models.Model):
    day = models.DateField(verbose_name=_("Day"), unique=True, db_index=True)

    class Meta:
        verbose_name = _("Bank holiday")
        verbose_name_plural = _("Bank holidays")
        ordering = ("day",)

    def __str__(self):
        return str(self.day)


auditlog.register(Invoice)
