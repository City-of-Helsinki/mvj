from enumfields.drf import EnumSupportSerializerMixin
from rest_framework import serializers

from users.models import User
from users.serializers import UserSerializer

from ..models import (
    Contact, District, Financing, Hitas, IntendedUse, Lease, LeaseIdentifier, LeaseType, Management, Municipality,
    NoticePeriod, Regulation, StatisticalUse, SupportiveHousing)
from .contact import ContactSerializer
from .contract import ContractCreateUpdateSerializer, ContractSerializer
from .decision import DecisionCreateUpdateNestedSerializer, DecisionSerializer
from .inspection import InspectionSerializer
from .land_area import LeaseAreaCreateUpdateSerializer, LeaseAreaSerializer
from .rent import LeaseBasisOfRentSerializer, RentCreateUpdateSerializer, RentSerializer
from .tenant import TenantCreateUpdateSerializer, TenantSerializer
from .utils import InstanceDictPrimaryKeyRelatedField, NameModelSerializer, UpdateNestedMixin


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


class LeaseTypeSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = LeaseType
        fields = '__all__'


class ManagementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Management
        fields = '__all__'


class MunicipalitySerializer(NameModelSerializer):
    class Meta:
        model = Municipality
        fields = '__all__'


class NoticePeriodSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = NoticePeriod
        fields = '__all__'


class RegulationSerializer(NameModelSerializer):
    class Meta:
        model = Regulation
        fields = '__all__'


class StatisticalUseSerializer(NameModelSerializer):
    class Meta:
        model = StatisticalUse
        fields = '__all__'


class SupportiveHousingSerializer(NameModelSerializer):
    class Meta:
        model = SupportiveHousing
        fields = '__all__'


class LeaseIdentifierSerializer(serializers.ModelSerializer):
    type = LeaseTypeSerializer()
    municipality = MunicipalitySerializer()
    district = DistrictSerializer()

    class Meta:
        model = LeaseIdentifier
        fields = ('type', 'municipality', 'district', 'sequence')


class LeaseSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    type = LeaseTypeSerializer()
    municipality = MunicipalitySerializer()
    district = DistrictSerializer()
    identifier = LeaseIdentifierSerializer(read_only=True)
    tenants = TenantSerializer(many=True, required=False, allow_null=True)
    lease_areas = LeaseAreaSerializer(many=True, required=False, allow_null=True)
    lessor = ContactSerializer(required=False, allow_null=True)
    contracts = ContractSerializer(many=True, required=False, allow_null=True)
    decisions = DecisionSerializer(many=True, required=False, allow_null=True)
    inspections = InspectionSerializer(many=True, required=False, allow_null=True)
    rents = RentSerializer(many=True, required=False, allow_null=True)
    basis_of_rents = LeaseBasisOfRentSerializer(many=True, required=False, allow_null=True)

    class Meta:
        model = Lease
        fields = '__all__'


class LeaseCreateUpdateSerializer(UpdateNestedMixin, EnumSupportSerializerMixin, serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    identifier = LeaseIdentifierSerializer(read_only=True)
    tenants = TenantCreateUpdateSerializer(many=True, required=False, allow_null=True)
    lease_areas = LeaseAreaCreateUpdateSerializer(many=True, required=False, allow_null=True)
    lessor = InstanceDictPrimaryKeyRelatedField(instance_class=Contact, queryset=Contact.objects.filter(is_lessor=True),
                                                related_serializer=ContactSerializer, required=False, allow_null=True)
    contracts = ContractCreateUpdateSerializer(many=True, required=False, allow_null=True)
    decisions = DecisionCreateUpdateNestedSerializer(many=True, required=False, allow_null=True)
    inspections = InspectionSerializer(many=True, required=False, allow_null=True)
    rents = RentCreateUpdateSerializer(many=True, required=False, allow_null=True)
    basis_of_rents = LeaseBasisOfRentSerializer(many=True, required=False, allow_null=True)
    preparer = InstanceDictPrimaryKeyRelatedField(instance_class=User, queryset=User.objects.all(),
                                                  related_serializer=UserSerializer, required=False, allow_null=True)

    class Meta:
        model = Lease
        fields = '__all__'
