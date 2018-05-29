from enumfields.drf import EnumSupportSerializerMixin
from rest_framework import serializers

from leasing.models import ConstructabilityDescription
from leasing.models.land_area import (
    LeaseAreaAddress, PlanUnitAddress, PlanUnitIntendedUse, PlotAddress, PlotDivisionState)
from users.models import User
from users.serializers import UserSerializer

from ..models import LeaseArea, PlanUnit, PlanUnitState, PlanUnitType, Plot
from .utils import InstanceDictPrimaryKeyRelatedField, NameModelSerializer, UpdateNestedMixin


class PlanUnitAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlanUnitAddress
        fields = ('id', 'address', 'postal_code', 'city')


class PlanUnitTypeSerializer(NameModelSerializer):
    class Meta:
        model = PlanUnitType
        fields = '__all__'


class PlanUnitStateSerializer(NameModelSerializer):
    class Meta:
        model = PlanUnitState
        fields = '__all__'


class PlanUnitIntendedUseSerializer(NameModelSerializer):
    class Meta:
        model = PlanUnitIntendedUse
        fields = '__all__'


class PlotDivisionStateSerializer(NameModelSerializer):
    class Meta:
        model = PlotDivisionState
        fields = '__all__'


class PlanUnitSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    addresses = PlanUnitAddressSerializer(many=True, required=False, allow_null=True)

    class Meta:
        model = PlanUnit
        fields = ('id', 'identifier', 'area', 'section_area', 'addresses', 'type', 'in_contract',
                  'plot_division_identifier', 'plot_division_date_of_approval', 'plot_division_state',
                  'detailed_plan_identifier', 'detailed_plan_latest_processing_date',
                  'detailed_plan_latest_processing_date_note', 'plan_unit_type', 'plan_unit_state',
                  'plan_unit_intended_use')


class PlanUnitCreateUpdateSerializer(EnumSupportSerializerMixin, UpdateNestedMixin, serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    addresses = PlanUnitAddressSerializer(many=True, required=False, allow_null=True)
    plan_unit_type = InstanceDictPrimaryKeyRelatedField(
        instance_class=PlanUnitType, queryset=PlanUnitType.objects.filter(), related_serializer=PlanUnitTypeSerializer)
    plan_unit_state = InstanceDictPrimaryKeyRelatedField(
        instance_class=PlanUnitState, queryset=PlanUnitState.objects.filter(),
        related_serializer=PlanUnitStateSerializer)
    plan_unit_intended_use = InstanceDictPrimaryKeyRelatedField(
        instance_class=PlanUnitIntendedUse, queryset=PlanUnitIntendedUse.objects.filter(),
        related_serializer=PlanUnitIntendedUseSerializer)
    plot_division_state = InstanceDictPrimaryKeyRelatedField(
        instance_class=PlotDivisionState, queryset=PlotDivisionState.objects.filter(),
        related_serializer=PlotDivisionStateSerializer)

    class Meta:
        model = PlanUnit
        fields = ('id', 'identifier', 'area', 'section_area', 'addresses', 'type', 'in_contract',
                  'plot_division_identifier', 'plot_division_date_of_approval', 'plot_division_state',
                  'detailed_plan_identifier', 'detailed_plan_latest_processing_date',
                  'detailed_plan_latest_processing_date_note', 'plan_unit_type', 'plan_unit_state',
                  'plan_unit_intended_use')


class PlotAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlotAddress
        fields = ('id', 'address', 'postal_code', 'city')


class PlotSerializer(EnumSupportSerializerMixin, UpdateNestedMixin, serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    addresses = PlotAddressSerializer(many=True, required=False, allow_null=True)

    class Meta:
        model = Plot
        fields = ('id', 'identifier', 'area', 'section_area', 'addresses', 'type', 'registration_date', 'repeal_date',
                  'in_contract')


class ConstructabilityDescriptionSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    user = UserSerializer()

    class Meta:
        model = ConstructabilityDescription
        fields = ('id', 'type', 'user', 'text', 'ahjo_reference_number', 'modified_at')


class ConstructabilityDescriptionCreateUpdateSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    user = UserSerializer(read_only=True, default=serializers.CurrentUserDefault())
    modified_at = serializers.ReadOnlyField()

    class Meta:
        model = ConstructabilityDescription
        fields = ('id', 'type', 'user', 'text', 'ahjo_reference_number', 'modified_at')


class LeaseAreaAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaseAreaAddress
        fields = ('id', 'address', 'postal_code', 'city')


class LeaseAreaSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    addresses = LeaseAreaAddressSerializer(many=True, required=False, allow_null=True)
    plots = PlotSerializer(many=True, required=False, allow_null=True)
    plan_units = PlanUnitSerializer(many=True, required=False, allow_null=True)
    polluted_land_planner = UserSerializer()
    constructability_descriptions = ConstructabilityDescriptionSerializer(many=True, required=False, allow_null=True)

    class Meta:
        model = LeaseArea
        fields = ('id', 'identifier', 'area', 'section_area', 'addresses', 'type', 'location', 'plots', 'plan_units',
                  'preconstruction_state', 'demolition_state', 'polluted_land_state',
                  'polluted_land_rent_condition_state', 'polluted_land_rent_condition_date', 'polluted_land_planner',
                  'polluted_land_projectwise_number', 'polluted_land_matti_report_number',
                  'constructability_report_state', 'constructability_report_investigation_state',
                  'constructability_report_signing_date', 'constructability_report_signer',
                  'constructability_report_geotechnical_number', 'other_state', 'constructability_descriptions')


class LeaseAreaCreateUpdateSerializer(EnumSupportSerializerMixin, UpdateNestedMixin, serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    addresses = LeaseAreaAddressSerializer(many=True, required=False, allow_null=True)
    plots = PlotSerializer(many=True, required=False, allow_null=True)
    plan_units = PlanUnitCreateUpdateSerializer(many=True, required=False, allow_null=True)
    polluted_land_planner = InstanceDictPrimaryKeyRelatedField(instance_class=User,
                                                               queryset=User.objects.all(),
                                                               related_serializer=UserSerializer, required=False,
                                                               allow_null=True)
    constructability_descriptions = ConstructabilityDescriptionCreateUpdateSerializer(many=True, required=False,
                                                                                      allow_null=True)

    class Meta:
        model = LeaseArea
        fields = ('id', 'identifier', 'area', 'section_area', 'addresses', 'type', 'location', 'plots', 'plan_units',
                  'preconstruction_state', 'demolition_state', 'polluted_land_state',
                  'polluted_land_rent_condition_state', 'polluted_land_rent_condition_date', 'polluted_land_planner',
                  'polluted_land_projectwise_number', 'polluted_land_matti_report_number',
                  'constructability_report_state', 'constructability_report_investigation_state',
                  'constructability_report_signing_date', 'constructability_report_signer',
                  'constructability_report_geotechnical_number', 'other_state', 'constructability_descriptions')
