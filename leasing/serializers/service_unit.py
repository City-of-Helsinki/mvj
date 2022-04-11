from rest_framework import serializers

from ..models import ServiceUnit


class ServiceUnitSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()

    class Meta:
        model = ServiceUnit
        fields = (
            "id",
            "name",
            # "description",
        )
