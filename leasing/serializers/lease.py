from enumfields.drf import EnumSupportSerializerMixin
from rest_framework import serializers

from leasing.models import (
    District, Financing, Hitas, IntendedUse, LeaseType, Management, Municipality, NoticePeriod, Regulation,
    StatisticalUse, SupportiveHousing)

from ..models import Lease, LeaseIdentifier
from .contact import ContactSerializer
from .tenant import TenantSerializer


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
        fields = '__all__'


class LeaseSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    identifier = LeaseIdentifierSerializer()
    tenants = TenantSerializer(many=True, required=False, allow_null=True)
    lessor = ContactSerializer()

    class Meta:
        model = Lease
        fields = '__all__'
