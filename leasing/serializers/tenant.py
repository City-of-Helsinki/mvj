from enumfields.drf import EnumSupportSerializerMixin
from rest_framework import serializers

from field_permissions.serializers import FieldPermissionsSerializerMixin
from leasing.models import RentIntendedUse
from leasing.models.tenant import TenantRentShare
from leasing.serializers.rent import RentIntendedUseSerializer

from ..models import Contact, Tenant, TenantContact
from .contact import ContactSerializer
from .utils import InstanceDictPrimaryKeyRelatedField, UpdateNestedMixin


class TenantContactSerializer(
    EnumSupportSerializerMixin,
    FieldPermissionsSerializerMixin,
    serializers.ModelSerializer,
):
    id = serializers.IntegerField(required=False)
    contact = ContactSerializer()

    class Meta:
        model = TenantContact
        fields = ("id", "type", "contact", "start_date", "end_date")


class TenantContactCreateUpdateSerializer(
    EnumSupportSerializerMixin,
    FieldPermissionsSerializerMixin,
    serializers.ModelSerializer,
):
    id = serializers.IntegerField(required=False)
    contact = InstanceDictPrimaryKeyRelatedField(
        instance_class=Contact,
        queryset=Contact.objects.all(),
        related_serializer=ContactSerializer,
    )

    class Meta:
        model = TenantContact
        fields = ("id", "type", "contact", "start_date", "end_date")


class TenantRentShareSerializer(
    FieldPermissionsSerializerMixin, serializers.ModelSerializer
):
    id = serializers.IntegerField(required=False)
    intended_use = RentIntendedUseSerializer()

    class Meta:
        model = TenantRentShare
        fields = ("id", "intended_use", "share_numerator", "share_denominator")


class TenantRentShareCreateUpdateSerializer(
    FieldPermissionsSerializerMixin, serializers.ModelSerializer
):
    id = serializers.IntegerField(required=False)
    intended_use = InstanceDictPrimaryKeyRelatedField(
        instance_class=RentIntendedUse,
        queryset=RentIntendedUse.objects.all(),
        related_serializer=RentIntendedUseSerializer,
    )

    class Meta:
        model = TenantRentShare
        fields = ("id", "intended_use", "share_numerator", "share_denominator")


class TenantSerializer(
    EnumSupportSerializerMixin,
    FieldPermissionsSerializerMixin,
    serializers.ModelSerializer,
):
    id = serializers.IntegerField(required=False)
    tenantcontact_set = TenantContactSerializer(
        many=True, required=False, allow_null=True
    )
    rent_shares = TenantRentShareSerializer(many=True, required=False, allow_null=True)

    class Meta:
        model = Tenant
        fields = (
            "id",
            "share_numerator",
            "share_denominator",
            "reference",
            "tenantcontact_set",
            "rent_shares",
        )


class TenantCreateUpdateSerializer(
    UpdateNestedMixin,
    EnumSupportSerializerMixin,
    FieldPermissionsSerializerMixin,
    serializers.ModelSerializer,
):
    id = serializers.IntegerField(required=False)
    tenantcontact_set = TenantContactCreateUpdateSerializer(
        many=True, required=False, allow_null=True
    )
    rent_shares = TenantRentShareCreateUpdateSerializer(
        many=True, required=False, allow_null=True
    )

    class Meta:
        model = Tenant
        fields = (
            "id",
            "share_numerator",
            "share_denominator",
            "reference",
            "tenantcontact_set",
            "rent_shares",
        )
