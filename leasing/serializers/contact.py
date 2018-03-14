from enumfields.drf import EnumSupportSerializerMixin
from rest_framework import serializers

from ..models import Contact


class ContactSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = Contact
        fields = '__all__'
