from auditlog.registry import auditlog
from django.db import models
from django.utils.translation import pgettext_lazy
from django.utils.translation import ugettext_lazy as _

from field_permissions.registry import field_permissions


class Inspection(models.Model):
    """
    In Finnish: Tarkastukset ja huomautukset
    """
    lease = models.ForeignKey('leasing.Lease', verbose_name=_("Lease"), related_name='inspections',
                              on_delete=models.PROTECT)

    # In Finnish: Tarkastaja
    inspector = models.CharField(verbose_name=_("Inspector"), null=True, blank=True, max_length=255)

    # In Finnish: Valvonta päivämäärä
    supervision_date = models.DateField(verbose_name=_("Supervision date"), null=True, blank=True)

    # In Finnish: Valvottu päivämäärä
    supervised_date = models.DateField(verbose_name=_("Supervised date"), null=True, blank=True)

    # In Finnish: Selite
    description = models.TextField(verbose_name=_("Description"), null=True, blank=True)

    recursive_get_related_skip_relations = ["lease"]

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Inspection")
        verbose_name_plural = pgettext_lazy("Model name", "Inspections")


auditlog.register(Inspection)

field_permissions.register(Inspection, exclude_fields=['lease'])
