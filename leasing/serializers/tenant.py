from enumfields.drf import EnumSupportSerializerMixin
from rest_framework import serializers

from field_permissions.serializers import FieldPermissionsSerializerMixin

from ..models import Contact, Tenant, TenantContact
from .contact import ContactSerializer
from .utils import InstanceDictPrimaryKeyRelatedField, UpdateNestedMixin


class TenantContactSerializer(EnumSupportSerializerMixin, FieldPermissionsSerializerMixin, serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    contact = ContactSerializer()

    class Meta:
        model = TenantContact
        fields = ('id', 'type', 'contact', 'start_date', 'end_date')


class TenantContactCreateUpdateSerializer(EnumSupportSerializerMixin, FieldPermissionsSerializerMixin,
                                          serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    contact = InstanceDictPrimaryKeyRelatedField(instance_class=Contact, queryset=Contact.objects.all(),
                                                 related_serializer=ContactSerializer)

    class Meta:
        model = TenantContact
        fields = ('id', 'type', 'contact', 'start_date', 'end_date')


class TenantSerializer(EnumSupportSerializerMixin, FieldPermissionsSerializerMixin, serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    tenantcontact_set = TenantContactSerializer(many=True, required=False, allow_null=True)

    class Meta:
        model = Tenant
        fields = ('id', 'share_numerator', 'share_denominator', 'reference', 'tenantcontact_set')


class TenantCreateUpdateSerializer(UpdateNestedMixin, EnumSupportSerializerMixin,
                                   FieldPermissionsSerializerMixin, serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    tenantcontact_set = TenantContactCreateUpdateSerializer(many=True, required=False, allow_null=True)

    class Meta:
        model = Tenant
        fields = ('id', 'share_numerator', 'share_denominator', 'reference', 'tenantcontact_set')
