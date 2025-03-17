from enumfields.drf import EnumSupportSerializerMixin
from rest_framework import serializers

from field_permissions.serializers import FieldPermissionsSerializerMixin
from leasing.models.periodic_rent_adjustment import (
    IndexPointFigureYearly,
    OldDwellingsInHousingCompaniesPriceIndex,
    PeriodicRentAdjustment,
)
from leasing.serializers.utils import InstanceDictPrimaryKeyRelatedField


class IndexPointFigureYearlySerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False)
    value = serializers.DecimalField(max_digits=8, decimal_places=1)
    year = serializers.IntegerField()
    region = serializers.CharField(max_length=255, required=False, allow_null=True)
    comment = serializers.CharField(required=False, allow_null=True)

    class Meta:
        model = IndexPointFigureYearly
        fields = ("id", "value", "year", "region", "comment")


class OldDwellingsInHousingCompaniesPriceIndexSerializer(
    FieldPermissionsSerializerMixin, serializers.ModelSerializer
):
    id = serializers.IntegerField(required=False)
    point_figures = IndexPointFigureYearlySerializer(
        many=True, required=False, allow_null=True
    )

    class Meta:
        model = OldDwellingsInHousingCompaniesPriceIndex
        fields = "__all__"


class PeriodicRentAdjustmentSerializer(
    EnumSupportSerializerMixin, serializers.ModelSerializer
):
    price_index = OldDwellingsInHousingCompaniesPriceIndexSerializer(
        required=False, allow_null=True
    )

    class Meta:
        model = PeriodicRentAdjustment
        fields = [
            "id",
            "adjustment_type",
            "price_index",
            "starting_point_figure_value",
            "starting_point_figure_year",
        ]


class PeriodicRentAdjustmentCreateUpdateSerializer(
    EnumSupportSerializerMixin, serializers.ModelSerializer
):
    price_index = InstanceDictPrimaryKeyRelatedField(
        instance_class=OldDwellingsInHousingCompaniesPriceIndex,
        queryset=OldDwellingsInHousingCompaniesPriceIndex.objects.all(),
        required=True,
        allow_null=False,
    )

    class Meta:
        model = PeriodicRentAdjustment
        fields = [
            "id",
            "adjustment_type",
            "price_index",
            "starting_point_figure_value",  # TODO needed? possible to take from backend?
            "starting_point_figure_year",  # TODO needed? possible to take from backend?
        ]

    def validate(self, data):
        # TODO remove after debugging if no need for custom validation
        return data

    def create(self, validated_data):
        # TODO if needed
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # TODO don't allow updating with null
        return super().update(instance, validated_data)
