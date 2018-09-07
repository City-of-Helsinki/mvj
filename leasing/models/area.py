from auditlog.registry import auditlog
from django.contrib.gis.db import models
from django.contrib.postgres.fields import JSONField
from django.utils.translation import pgettext_lazy
from django.utils.translation import ugettext_lazy as _
from enumfields import EnumField

from leasing.enums import AreaType

from .mixins import NameModel, TimeStampedSafeDeleteModel


class AreaSource(NameModel):
    class Meta(NameModel.Meta):
        verbose_name = pgettext_lazy("Model name", "Area source")
        verbose_name_plural = pgettext_lazy("Model name", "Area source")


class Area(TimeStampedSafeDeleteModel):
    """
    In Finnish: Alue
    """
    type = EnumField(AreaType, verbose_name=_("Area type"), max_length=30)
    identifier = models.CharField(verbose_name=_("Identifier"), max_length=255)
    external_id = models.CharField(verbose_name=_("External ID"), max_length=255)
    geometry = models.MultiPolygonField(srid=4326, verbose_name=_("Geometry"), null=True, blank=True)
    metadata = JSONField(verbose_name=_("Metadata"), null=True, blank=True)
    source = models.ForeignKey(AreaSource, verbose_name=_("Source"), related_name='areas', null=True, blank=True,
                               on_delete=models.PROTECT)

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Area")
        verbose_name_plural = pgettext_lazy("Model name", "Area")


auditlog.register(Area)
