from rest_framework import serializers

from ..models import Inspection


class InspectionSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = Inspection
        fields = ('id', 'inspector', 'supervision_date', 'supervised_date', 'description')
