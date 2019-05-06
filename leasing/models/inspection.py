from auditlog.registry import auditlog
from django.db import models
from django.utils.translation import pgettext_lazy
from django.utils.translation import ugettext_lazy as _

from field_permissions.registry import field_permissions
from leasing.models.mixins import TimeStampedSafeDeleteModel
from users.models import User


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


def get_inspection_attachment_file_upload_to(instance, filename):
    return '/'.join(['inspection_attachments', str(instance.inspection.id), filename])


class InspectionAttachment(TimeStampedSafeDeleteModel):
    """
    In Finnish: Liitetiedosto (Tarkastus/Huomautus)
    """
    inspection = models.ForeignKey(Inspection, related_name='attachments', on_delete=models.PROTECT)

    # In Finnish: Tiedosto
    file = models.FileField(upload_to=get_inspection_attachment_file_upload_to, blank=False, null=False)

    # In Finnish: Lataaja
    uploader = models.ForeignKey(User, verbose_name=_("Uploader"), related_name='+', on_delete=models.PROTECT)

    # In Finnish: Latausaika
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Time uploaded"))

    recursive_get_related_skip_relations = ["inspection", "uploader"]

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Inspection attachment")
        verbose_name_plural = pgettext_lazy("Model name", "Inspection attachments")


auditlog.register(Inspection)

field_permissions.register(Inspection, exclude_fields=['lease'])
