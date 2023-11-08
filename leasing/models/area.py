from django.contrib.gis.db import models
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models as djmodels
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy
from enumfields import EnumField

from leasing.enums import AreaType
from leasing.models.utils import denormalize_identifier, normalize_identifier

from .mixins import NameModel, TimeStampedModel


class AreaSource(NameModel):
    identifier = models.CharField(
        verbose_name=_("Identifier"), max_length=255, unique=True
    )

    class Meta(NameModel.Meta):
        verbose_name = pgettext_lazy("Model name", "Area source")
        verbose_name_plural = pgettext_lazy("Model name", "Area source")


class Area(TimeStampedModel):
    """
    In Finnish: Alue
    """

    type = EnumField(AreaType, verbose_name=_("Area type"), max_length=31)
    identifier = models.CharField(verbose_name=_("Identifier"), max_length=255)
    external_id = models.CharField(verbose_name=_("External ID"), max_length=255)
    geometry = models.MultiPolygonField(
        srid=4326, verbose_name=_("Geometry"), null=True, blank=True
    )
    metadata = djmodels.JSONField(
        verbose_name=_("Metadata"), encoder=DjangoJSONEncoder, null=True, blank=True
    )
    source = models.ForeignKey(
        AreaSource,
        verbose_name=_("Source"),
        related_name="areas",
        on_delete=models.PROTECT,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["type", "identifier", "external_id", "source"],
                name="leasing_area_type_identifier_externalid_source_key",
            )
        ]
        verbose_name = pgettext_lazy("Model name", "Area")
        verbose_name_plural = pgettext_lazy("Model name", "Area")

    def get_land_identifier(self):
        return "{}-{}-{}-{}{}".format(
            self.metadata.get("municipality", "0")
            if self.metadata.get("municipality")
            else "0",
            self.metadata.get("district", "0")
            if self.metadata.get("district")
            else "0",
            self.metadata.get("group", "0") if self.metadata.get("group") else "0",
            self.metadata.get("unit", "0") if self.metadata.get("unit") else "0",
            "-{}".format(self.metadata.get("mvj_unit", "0"))
            if "mvj_unit" in self.metadata
            else "",
        )

    def get_normalized_identifier(self):
        return normalize_identifier(self.get_land_identifier())

    def get_denormalized_identifier(self):
        return denormalize_identifier(self.identifier)
