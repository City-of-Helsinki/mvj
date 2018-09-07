from auditlog.registry import auditlog
from django.contrib.gis.db import models
from django.utils.translation import pgettext_lazy
from django.utils.translation import ugettext_lazy as _

from users.models import User

from .mixins import TimeStampedSafeDeleteModel


class AreaNote(TimeStampedSafeDeleteModel):
    """
    In Finnish: Muistettava ehto
    """
    # In Finnish: Alue
    # geometry = models.MultiPolygonField(srid=4326, verbose_name=_("Geometry"), null=True, blank=True)
    geometry = models.MultiPolygonField(srid=4326, null=True, blank=True)

    # In Finnish: Kommentti
    note = models.TextField(verbose_name=_("Note"), null=True, blank=True)
    user = models.ForeignKey(User, verbose_name=_("User"), on_delete=models.PROTECT)

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Area note")
        verbose_name_plural = pgettext_lazy("Model name", "Area notes")


auditlog.register(AreaNote)
