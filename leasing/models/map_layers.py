from django.core.validators import RegexValidator
from django.db import models
from django.utils.translation import get_language

from leasing.models.land_area import LeaseArea


class HexColorValidator(RegexValidator):
    # Startswith `#`, then has either 1 or 2 groups of 3 characters
    # that are 0-9 or a-f or A-F
    regex = r"^#(?:[0-9a-fA-F]{3}){1,2}$"
    message = "Enter a valid hex color code, e.g. #000000 or #FFF"


class VipunenMapLayer(models.Model):
    """Tree structure of categories for Vipunen map layers."""

    filter_by_lease_type = models.ForeignKey(
        "leasing.LeaseType",
        on_delete=models.SET_NULL,
        related_name="map_layers",
        null=True,
        blank=True,
    )
    filter_by_intended_use = models.ForeignKey(
        "leasing.IntendedUse",
        on_delete=models.SET_NULL,
        related_name="map_layers",
        null=True,
        blank=True,
    )
    filter_by_service_unit = models.ForeignKey(
        "leasing.ServiceUnit",
        on_delete=models.SET_NULL,
        related_name="map_layers",
        null=True,
        blank=True,
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children",
    )
    order_in_parent = models.IntegerField(blank=True, null=True)
    name_fi = models.CharField(max_length=255)
    name_sv = models.CharField(max_length=255, blank=True, null=True)
    name_en = models.CharField(max_length=255, blank=True, null=True)
    keywords = models.CharField(max_length=255, blank=True, null=True)
    hex_color = models.CharField(
        max_length=7,
        blank=True,
        null=True,
        validators=[HexColorValidator()],
    )

    class Meta:
        permissions = [
            # Access to the model via Export API
            ("export_api_vipunen_map_layer", "Can access export API vipunen map layer"),
        ]

    def __str__(self):
        name = self.get_name()
        layer = self
        while layer.parent:
            name = f"{layer.parent.get_name()} > {name}"
            layer = layer.parent
        return name

    def get_name(self):
        language = get_language()
        if language == "fi" and self.name_fi is not None:
            return self.name_fi
        elif language == "sv" and self.name_sv is not None:
            return self.name_sv
        elif language == "en" and self.name_en is not None:
            return self.name_en
        return self.name_fi or ""

    @classmethod
    def get_map_layer_ids_for_lease_area(cls, lease_area: LeaseArea):
        """Get all map layer ids for a lease area,
        based on the matching attributes of LeaseType, IntendedUse and ServiceUnit."""

        layer_ids_qs = cls.objects.none()
        if lease_area.lease.type:
            lease_type_qs = cls.objects.filter(lease_type=lease_area.lease.type)
            layer_ids_qs = layer_ids_qs.union(lease_type_qs)

        if lease_area.lease.intended_use:
            intended_use_qs = cls.objects.filter(
                intended_use=lease_area.lease.intended_use
            )
            layer_ids_qs = layer_ids_qs.union(intended_use_qs)

        if lease_area.lease.service_unit:
            service_unit_qs = cls.objects.filter(
                service_unit=lease_area.lease.service_unit
            )
            layer_ids_qs = layer_ids_qs.union(service_unit_qs)

        return layer_ids_qs.values_list("id", flat=True)
