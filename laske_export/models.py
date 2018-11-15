from auditlog.registry import auditlog
from django.db import models
from django.utils.translation import pgettext_lazy
from django.utils.translation import ugettext_lazy as _

from leasing.models import Invoice
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

    invoices = models.ManyToManyField(Invoice)

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Laske export log")
        verbose_name_plural = pgettext_lazy("Model name", "Laske export logs")
        ordering = ['-created_at']


auditlog.register(LaskeExportLog)
