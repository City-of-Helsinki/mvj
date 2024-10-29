from rest_framework import serializers

from leasing.models import ReceivableType


class ReceivableTypeSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = ReceivableType
        fields = "__all__"
