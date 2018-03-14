from enumfields.drf import EnumSupportSerializerMixin
from rest_framework import serializers

from leasing.serializers.land_area import LeaseAreaCreateUpdateSerializer, LeaseAreaSerializer

from ..models import (
    Contact, District, Financing, Hitas, IntendedUse, Lease, LeaseIdentifier, LeaseType, Management, Municipality,
    NoticePeriod, Regulation, StatisticalUse, SupportiveHousing)
from .contact import ContactSerializer
from .tenant import TenantCreateUpdateSerializer, TenantSerializer
from .utils import InstanceDictPrimaryKeyRelatedField, UpdateNestedMixin


class DistrictSerializer(serializers.ModelSerializer):
    class Meta:
        model = District
        fields = '__all__'


class FinancingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Financing
        fields = '__all__'


class HitasSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hitas
        fields = '__all__'


class IntendedUseSerializer(serializers.ModelSerializer):
    class Meta:
        model = IntendedUse
        fields = '__all__'


class LeaseTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaseType
        fields = '__all__'


class ManagementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Management
        fields = '__all__'


class MunicipalitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Municipality
        fields = '__all__'


class NoticePeriodSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = NoticePeriod
        fields = '__all__'


class RegulationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Regulation
        fields = '__all__'


class StatisticalUseSerializer(serializers.ModelSerializer):
    class Meta:
        model = StatisticalUse
        fields = '__all__'


class SupportiveHousingSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportiveHousing
        fields = '__all__'


class LeaseIdentifierSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaseIdentifier
        fields = ('type', 'municipality', 'district', 'sequence')


class LeaseSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    identifier = LeaseIdentifierSerializer(read_only=True)
    tenants = TenantSerializer(many=True, required=False, allow_null=True)
    lease_areas = LeaseAreaSerializer(many=True, required=False, allow_null=True)
    lessor = ContactSerializer()

    class Meta:
        model = Lease
        fields = '__all__'


class LeaseCreateUpdateSerializer(UpdateNestedMixin, EnumSupportSerializerMixin, serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    identifier = LeaseIdentifierSerializer(read_only=True)
    tenants = TenantCreateUpdateSerializer(many=True, required=False, allow_null=True)
    lease_areas = LeaseAreaCreateUpdateSerializer(many=True, required=False, allow_null=True)
    lessor = InstanceDictPrimaryKeyRelatedField(instance_class=Contact, queryset=Contact.objects.filter(is_lessor=True),
                                                related_serializer=ContactSerializer)

    class Meta:
        model = Lease
        fields = '__all__'
