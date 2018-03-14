from enumfields.drf import EnumSupportSerializerMixin
from rest_framework import serializers

from leasing.models import PlanUnitState, PlanUnitType

from ..models import LeaseArea, PlanUnit, Plot
from .utils import InstanceDictPrimaryKeyRelatedField, UpdateNestedMixin


class NameModelSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    name = serializers.CharField(read_only=True)


class PlanUnitTypeSerializer(NameModelSerializer):
    class Meta:
        model = PlanUnitType
        fields = '__all__'


class PlanUnitStateSerializer(NameModelSerializer):
    class Meta:
        model = PlanUnitState
        fields = '__all__'


class PlanUnitSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    plan_unit_type = InstanceDictPrimaryKeyRelatedField(
        instance_class=PlanUnitType, queryset=PlanUnitType.objects.filter(), related_serializer=PlanUnitTypeSerializer)
    plan_unit_state = InstanceDictPrimaryKeyRelatedField(
        instance_class=PlanUnitState, queryset=PlanUnitState.objects.filter(),
        related_serializer=PlanUnitTypeSerializer)

    class Meta:
        model = PlanUnit
        fields = ('id', 'identifier', 'area', 'section_area', 'address', 'postal_code', 'city', 'type',
                  'in_contract', 'plot_division_identifier', 'plot_division_date_of_approval',
                  'detailed_plan_identifier', 'detailed_plan_date_of_approval', 'plan_unit_type', 'plan_unit_state')


class PlotSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = Plot
        fields = ('id', 'identifier', 'area', 'section_area', 'address', 'postal_code', 'city', 'type',
                  'registration_date', 'in_contract')


class LeaseAreaSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    plots = PlotSerializer(many=True, required=False, allow_null=True)
    plan_units = PlanUnitSerializer(many=True, required=False, allow_null=True)

    class Meta:
        model = LeaseArea
        fields = ('id', 'identifier', 'area', 'section_area', 'address', 'postal_code', 'city', 'type', 'location',
                  'plots', 'plan_units')


class LeaseAreaCreateUpdateSerializer(UpdateNestedMixin, EnumSupportSerializerMixin, serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    plots = PlotSerializer(many=True, required=False, allow_null=True)
    plan_units = PlanUnitSerializer(many=True, required=False, allow_null=True)

    class Meta:
        model = LeaseArea
        fields = ('id', 'identifier', 'area', 'section_area', 'address', 'postal_code', 'city', 'type', 'location',
                  'plots', 'plan_units')
