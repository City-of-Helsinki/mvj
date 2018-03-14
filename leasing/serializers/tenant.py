from enumfields.drf import EnumSupportSerializerMixin
from rest_framework import serializers

from ..models import Contact, Tenant, TenantContact
from .contact import ContactSerializer
from .utils import InstanceDictPrimaryKeyRelatedField, UpdateNestedMixin


class TenantContactSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    contact = InstanceDictPrimaryKeyRelatedField(instance_class=Contact, queryset=Contact.objects.all(),
                                                 related_serializer=ContactSerializer)

    class Meta:
        model = TenantContact
        fields = ('id', 'type', 'contact', 'start_date', 'end_date')


class TenantSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    tenantcontact_set = TenantContactSerializer(many=True, required=False, allow_null=True)

    class Meta:
        model = Tenant
        fields = ('id', 'share_numerator', 'share_denominator', 'reference', 'tenantcontact_set')


class TenantCreateUpdateSerializer(UpdateNestedMixin, EnumSupportSerializerMixin, serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    tenantcontact_set = TenantContactSerializer(many=True, required=False, allow_null=True)

    class Meta:
        model = Tenant
        fields = ('id', 'share_numerator', 'share_denominator', 'reference', 'tenantcontact_set')
