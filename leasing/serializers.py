from enumfields.drf import EnumSupportSerializerMixin
from rest_framework import serializers

from leasing.models import Lease


class LeaseSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    identifier = serializers.ReadOnlyField(source='identifier_string')

    class Meta:
        model = Lease
        fields = '__all__'
