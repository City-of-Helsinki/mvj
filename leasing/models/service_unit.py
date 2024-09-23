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
    abbreviation = models.CharField(verbose_name=_("Abbreviation"), max_length=15)
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
    laske_fill_priority_and_info = models.BooleanField(
        verbose_name=_("Fill priority and info?"),
        help_text=_(
            "Fill Info and Priority data from a contact into OrderParty and"
            " BillingParty in SalesOrder when creating LASKE XML"
        ),
        default=True,
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
    default_receivable_type_rent = models.ForeignKey(
        "leasing.ReceivableType",
        verbose_name=_("Default receivable type (rent)"),
        help_text=_("Receivable type used when creating rent invoices"),
        related_name="+",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )
    default_receivable_type_collateral = models.ForeignKey(
        "leasing.ReceivableType",
        verbose_name=_("Default receivable type (collateral)"),
        help_text=_(
            "Receivable type which should be used when creating collateral invoices. "
            "On SAP export, the profit center is filled from this receivable type's "
            "sap_order_item_number."
        ),
        related_name="+",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )

    recursive_get_related_skip_relations = [
        "contacts",
        "leases",
        "invoices",
        "users",
        "groups",
        "receivable_types",
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
