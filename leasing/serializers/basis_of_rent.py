from enumfields.drf import EnumSupportSerializerMixin
from rest_framework import serializers

from ..models import (
    BasisOfRent, BasisOfRentBuildPermissionType, BasisOfRentDecision, BasisOfRentPlotType,
    BasisOfRentPropertyIdentifier, BasisOfRentRate, DecisionMaker)
from .decision import DecisionMakerSerializer
from .utils import InstanceDictPrimaryKeyRelatedField, NameModelSerializer, UpdateNestedMixin


class BasisOfRentPlotTypeSerializer(NameModelSerializer):
    class Meta:
        model = BasisOfRentPlotType
        fields = '__all__'


class BasisOfRentBuildPermissionTypeSerializer(NameModelSerializer):
    class Meta:
        model = BasisOfRentBuildPermissionType
        fields = '__all__'


class BasisOfRentDecisionSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    decision_maker = InstanceDictPrimaryKeyRelatedField(
        instance_class=DecisionMaker, queryset=DecisionMaker.objects.filter(),
        related_serializer=DecisionMakerSerializer, required=False, allow_null=True)

    class Meta:
        model = BasisOfRentDecision
        fields = ('id', 'reference_number', 'decision_maker', 'decision_date', 'section')


class BasisOfRentPropertyIdentifierSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = BasisOfRentPropertyIdentifier
        fields = ('id', 'identifier')


class BasisOfRentRateSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    build_permission_type = InstanceDictPrimaryKeyRelatedField(
        instance_class=BasisOfRentBuildPermissionType, queryset=BasisOfRentBuildPermissionType.objects.all(),
        related_serializer=BasisOfRentBuildPermissionTypeSerializer)

    class Meta:
        model = BasisOfRentRate
        fields = ('id', 'build_permission_type', 'amount', 'area_unit')


class BasisOfRentSerializer(serializers.ModelSerializer):
    plot_type = BasisOfRentPlotTypeSerializer()
    rent_rates = BasisOfRentRateSerializer(many=True, required=False, allow_null=True)
    property_identifiers = BasisOfRentPropertyIdentifierSerializer(many=True, required=False, allow_null=True)
    decisions = BasisOfRentDecisionSerializer(many=True, required=False, allow_null=True)

    class Meta:
        model = BasisOfRent
        fields = ('id', 'plot_type', 'start_date', 'end_date', 'detailed_plan_identifier', 'management', 'financing',
                  'lease_rights_end_date', 'index', 'note', 'created_at', 'modified_at', 'rent_rates',
                  'property_identifiers', 'decisions')


class BasisOfRentCreateUpdateSerializer(UpdateNestedMixin, serializers.ModelSerializer):
    rent_rates = BasisOfRentRateSerializer(many=True, required=False, allow_null=True)
    property_identifiers = BasisOfRentPropertyIdentifierSerializer(many=True, required=False, allow_null=True)
    decisions = BasisOfRentDecisionSerializer(many=True, required=False, allow_null=True)

    class Meta:
        model = BasisOfRent
        fields = ('id', 'plot_type', 'start_date', 'end_date', 'detailed_plan_identifier', 'management', 'financing',
                  'lease_rights_end_date', 'index', 'note', 'created_at', 'modified_at', 'rent_rates',
                  'property_identifiers', 'decisions')
