from rest_framework import serializers
from rest_framework_gis.serializers import GeoModelSerializer

from users.serializers import UserSerializer

from ..models import AreaNote


class AreaNoteSerializer(GeoModelSerializer):
    id = serializers.ReadOnlyField()
    user = UserSerializer(read_only=True)

    class Meta:
        model = AreaNote
        fields = '__all__'


class AreaNoteCreateUpdateSerializer(GeoModelSerializer):
    id = serializers.ReadOnlyField()
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = AreaNote
        fields = '__all__'
