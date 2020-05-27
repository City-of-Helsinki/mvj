from django_countries.serializers import CountryFieldMixin
from enumfields.drf import EnumSupportSerializerMixin
from rest_framework import serializers

from field_permissions.serializers import FieldPermissionsSerializerMixin

from ..models import Contact


class ContactSerializer(
    EnumSupportSerializerMixin,
    CountryFieldMixin,
    FieldPermissionsSerializerMixin,
    serializers.ModelSerializer,
):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = Contact
        fields = "__all__"
