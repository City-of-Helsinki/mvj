from enumfields.drf import EnumSupportSerializerMixin
from rest_framework import serializers

from ..models import (
    BasisOfRent, BasisOfRentDecision, BasisOfRentPlotType, BasisOfRentPropertyIdentifier, BasisOfRentRate,
    RentIntendedUse)
from .rent import RentIntendedUseSerializer
from .utils import InstanceDictPrimaryKeyRelatedField, NameModelSerializer, UpdateNestedMixin


class BasisOfRentPlotTypeSerializer(NameModelSerializer):
    class Meta:
        model = BasisOfRentPlotType
        fields = '__all__'


class BasisOfRentDecisionSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = BasisOfRentDecision
        fields = ('id', 'identifier')


class BasisOfRentPropertyIdentifierSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = BasisOfRentPropertyIdentifier
        fields = ('id', 'identifier')


class BasisOfRentRateSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    intended_use = InstanceDictPrimaryKeyRelatedField(instance_class=RentIntendedUse,
                                                      queryset=RentIntendedUse.objects.all(),
                                                      related_serializer=RentIntendedUseSerializer)

    class Meta:
        model = BasisOfRentRate
        fields = ('id', 'intended_use', 'amount', 'period')


class BasisOfRentSerializer(serializers.ModelSerializer):
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
