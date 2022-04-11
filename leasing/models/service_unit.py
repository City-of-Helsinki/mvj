from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy

from leasing.models.mixins import TimeStampedSafeDeleteModel


class ServiceUnit(TimeStampedSafeDeleteModel):
    """
    In Finnish: Palvelukokonaisuus
    """

    name = models.CharField(verbose_name=_("Name"), max_length=255)
    description = models.TextField(verbose_name=_("Description"), null=True, blank=True)
    laske_sender_id = models.CharField(
        verbose_name=_("Sender ID in Laske"), max_length=255
    )
    laske_import_id = models.CharField(
        verbose_name=_("Import ID in Laske"), max_length=255
    )
    laske_sales_org = models.CharField(
        verbose_name=_("Sales Organisation in Laske"), max_length=255
    )

    recursive_get_related_skip_relations = ["contacts", "leases", "invoices", "users"]

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Service unit")
        verbose_name_plural = pgettext_lazy("Model name", "Service units")

    def __str__(self):
        return self.name
