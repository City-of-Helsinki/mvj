from django.db import models
from django.utils.translation import get_language

from leasing.models.land_area import LeaseArea
from leasing.validators import HexColorValidator


class VipunenMapLayer(models.Model):
    """Tree structure of categories for Vipunen map layers."""

    filter_by_lease_type = models.ManyToManyField(
        "leasing.LeaseType",
        related_name="map_layers",
        blank=True,
    )
    filter_by_intended_use = models.ManyToManyField(
        "leasing.IntendedUse",
        related_name="map_layers",
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

        map_layers = (
            cls.objects.all()
            .select_related("filter_by_service_unit")
            .prefetch_related("filter_by_lease_type", "filter_by_intended_use")
        )

        matching_layer_ids = set()

        lease_type_id = lease_area.lease.type.id if lease_area.lease.type else None
        lease_intended_use_id = (
            lease_area.lease.intended_use.id if lease_area.lease.intended_use else None
        )
        lease_service_unit_id = (
            lease_area.lease.service_unit.id if lease_area.lease.service_unit else None
        )

        for layer in map_layers:
            filter_by_lease_type_ids: set = {
                lease_type.id for lease_type in layer.filter_by_lease_type.all()
            }
            filter_by_intended_use_ids: set = {
                intended_use.id for intended_use in layer.filter_by_intended_use.all()
            }
            has_lease_type_filter = bool(filter_by_lease_type_ids)
            has_intended_use_filter = bool(filter_by_intended_use_ids)
            has_service_unit_filter = layer.filter_by_service_unit is not None

            # If no filters are set on this layer, it doesn't match any LeaseArea
            if not (
                has_lease_type_filter
                or has_intended_use_filter
                or has_service_unit_filter
            ):
                continue

            if has_lease_type_filter and (
                not lease_type_id or lease_type_id not in filter_by_lease_type_ids
            ):
                continue

            if has_intended_use_filter and (
                not lease_intended_use_id
                or lease_intended_use_id not in filter_by_intended_use_ids
            ):
                continue

            if has_service_unit_filter and (
                not lease_service_unit_id
                or layer.filter_by_service_unit.id != lease_service_unit_id
            ):
                continue

            # The LeaseArea matched all filters set on this map layer
            matching_layer_ids.add(layer.id)

        return list(matching_layer_ids)
