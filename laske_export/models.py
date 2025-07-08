from auditlog.registry import auditlog
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy
from enumfields import EnumField

from laske_export.enums import LaskeExportLogInvoiceStatus
from leasing.models import Invoice
from leasing.models.invoice import InvoicePayment
from leasing.models.land_use_agreement import LandUseAgreementInvoice
from leasing.models.mixins import TimeStampedSafeDeleteModel


class LaskeExportLog(TimeStampedSafeDeleteModel):
    """
    In Finnish: Vientiloki
    """

    # In Finnish: Aloitusaika
    started_at = models.DateTimeField(verbose_name=_("Time started"))

    # In Finnish: Lopetusaika
    ended_at = models.DateTimeField(verbose_name=_("Time ended"), null=True, blank=True)

    # In Finnish: Valmis?
    is_finished = models.BooleanField(verbose_name=_("Finished?"), default=False)

    # In Finnish: Tiedostonimi
    filename = models.CharField(max_length=255, blank=True, verbose_name=_("Filename"))

    # In Finnish: Palvelukokonaisuus
    service_unit = models.ForeignKey(
        "leasing.ServiceUnit",
        verbose_name=_("Service unit"),
        related_name="+",
        on_delete=models.PROTECT,
    )

    invoices = models.ManyToManyField(Invoice, through="LaskeExportLogInvoiceItem")

    land_use_agreement_invoices = models.ManyToManyField(LandUseAgreementInvoice)

    recursive_get_related_skip_relations = [
        "service_unit",
    ]

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Laske export log")
        verbose_name_plural = pgettext_lazy("Model name", "Laske export logs")
        ordering = ["-created_at"]


class LaskeExportLogInvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE)
    laskeexportlog = models.ForeignKey(LaskeExportLog, on_delete=models.CASCADE)

    # In Finnish: Tila
    status = EnumField(
        LaskeExportLogInvoiceStatus,
        null=True,
        blank=True,
        max_length=255,
        verbose_name=_("status"),
    )

    # In Finnish: Informaatio
    information = models.TextField(blank=True, verbose_name=_("information"))


class LaskePaymentsLog(TimeStampedSafeDeleteModel):
    """
    In Finnish: Varjoreskontraloki
    """

    # In Finnish: Tiedostonimi
    filename = models.CharField(max_length=255, verbose_name=_("Filename"))

    # In Finnish: Aloitusaika
    started_at = models.DateTimeField(verbose_name=_("Time started"))

    # In Finnish: Lopetusaika
    ended_at = models.DateTimeField(verbose_name=_("Time ended"), null=True, blank=True)

    # In Finnish: Valmis?
    is_finished = models.BooleanField(verbose_name=_("Finished?"), default=False)

    payments = models.ManyToManyField(InvoicePayment)

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Laske payments log")
        verbose_name_plural = pgettext_lazy("Model name", "Laske payments logs")
        ordering = ["-created_at"]


auditlog.register(LaskeExportLog)
auditlog.register(LaskePaymentsLog)
