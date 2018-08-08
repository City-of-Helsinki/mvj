from rest_framework import serializers

from users.serializers import UserSerializer

from ..models import AreaNote


class AreaNoteSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    user = UserSerializer(read_only=True)

    class Meta:
        model = AreaNote
        fields = '__all__'


class AreaNoteCreateUpdateSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = AreaNote
        fields = '__all__'
