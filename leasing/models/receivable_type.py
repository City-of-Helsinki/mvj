from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy


class ReceivableType(models.Model):
    """
    In Finnish: Saamislaji
    """

    name = models.CharField(verbose_name=_("Name"), max_length=255)
    sap_material_code = models.CharField(
        verbose_name=_("SAP material code"), null=True, blank=True, max_length=255
    )
    sap_order_item_number = models.CharField(
        verbose_name=_("SAP order item number"),
        null=True,
        blank=True,
        max_length=255,
        help_text=_(
            "If 'SAP project number' is set, it will be used instead of this value."
        ),
    )
    sap_project_number = models.CharField(
        verbose_name=_("SAP project number"),
        null=True,
        blank=True,
        max_length=255,
        help_text=_(
            "This field takes priority over 'SAP order item number' if both are set."
        ),
    )
    is_active = models.BooleanField(verbose_name=_("Is active?"), default=True)
    service_unit = models.ForeignKey(
        "leasing.ServiceUnit",
        verbose_name=_("Service unit"),
        related_name="receivable_types",
        on_delete=models.PROTECT,
    )

    recursive_get_related_skip_relations = [
        "service_unit",
    ]

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Receivable type")
        verbose_name_plural = pgettext_lazy("Model name", "Receivable types")

    def __str__(self):
        return self.name
