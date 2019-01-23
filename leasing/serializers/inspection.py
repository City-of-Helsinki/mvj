from rest_framework import serializers

from field_permissions.serializers import FieldPermissionsSerializerMixin

from ..models import Inspection


class InspectionSerializer(FieldPermissionsSerializerMixin, serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = Inspection
        fields = ('id', 'inspector', 'supervision_date', 'supervised_date', 'description')
