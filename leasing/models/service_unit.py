from django.contrib.auth.models import Group
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
    invoice_number_sequence_name = models.CharField(
        verbose_name=_("Invoice number sequence name"),
        max_length=255,
        null=True,
        blank=True,
    )
    first_invoice_number = models.IntegerField(
        verbose_name=_("First invoice number"), null=True, blank=True
    )
    laske_sender_id = models.CharField(
        verbose_name=_("Sender ID in Laske"), max_length=255
    )
    laske_import_id = models.CharField(
        verbose_name=_("Import ID in Laske"), max_length=255
    )
    laske_sales_org = models.CharField(
        verbose_name=_("Sales Organisation in Laske"), max_length=255
    )
    contract_number_sequence_name = models.CharField(
        verbose_name=_("Contract number sequence name"),
        max_length=255,
        null=True,
        blank=True,
    )
    first_contract_number = models.IntegerField(
        verbose_name=_("First contract number"), null=True, blank=True
    )

    recursive_get_related_skip_relations = [
        "contacts",
        "leases",
        "invoices",
        "users",
        "groups",
    ]

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Service unit")
        verbose_name_plural = pgettext_lazy("Model name", "Service units")

    def __str__(self):
        return self.name


class ServiceUnitGroupMapping(models.Model):
    group = models.ForeignKey(
        Group, on_delete=models.CASCADE, related_name="service_units"
    )
    service_unit = models.ForeignKey(
        ServiceUnit, on_delete=models.CASCADE, related_name="groups"
    )

    def __str__(self):
        return f"{self.group} -> {self.service_unit}"

    class Meta:
        unique_together = ("group", "service_unit")
        verbose_name = pgettext_lazy("Model name", "Service unit group mapping")
        verbose_name_plural = pgettext_lazy("Model name", "Service unit group mappings")
