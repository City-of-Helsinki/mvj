from enumfields.drf import EnumSupportSerializerMixin
from rest_framework import serializers

from ..models import Tenant
from .contact import ContactSerializer


class TenantSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    contacts = ContactSerializer(many=True, required=False, allow_null=True)

    class Meta:
        model = Tenant
        fields = '__all__'
