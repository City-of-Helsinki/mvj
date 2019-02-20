from rest_framework import serializers

from users.serializers import UserSerializer

from ..models import UiData


class UiDataSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    user = UserSerializer(read_only=True)

    class Meta:
        model = UiData
        fields = '__all__'


class UiDataCreateUpdateSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()

    class Meta:
        model = UiData
        fields = '__all__'
