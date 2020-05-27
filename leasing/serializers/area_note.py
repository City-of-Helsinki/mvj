from rest_framework import serializers

from field_permissions.serializers import FieldPermissionsSerializerMixin
from users.serializers import UserSerializer

from ..models import AreaNote


class AreaNoteSerializer(FieldPermissionsSerializerMixin, serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    user = UserSerializer(read_only=True)

    class Meta:
        model = AreaNote
        fields = "__all__"


class AreaNoteCreateUpdateSerializer(
    FieldPermissionsSerializerMixin, serializers.ModelSerializer
):
    id = serializers.ReadOnlyField()
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = AreaNote
        fields = "__all__"
