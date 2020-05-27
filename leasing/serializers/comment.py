from rest_framework import serializers

from field_permissions.serializers import FieldPermissionsSerializerMixin
from users.serializers import UserSerializer

from ..models import Comment, CommentTopic
from .utils import InstanceDictPrimaryKeyRelatedField


class CommentTopicSerializer(
    FieldPermissionsSerializerMixin, serializers.ModelSerializer
):
    id = serializers.ReadOnlyField()

    class Meta:
        model = CommentTopic
        fields = "__all__"


class CommentSerializer(FieldPermissionsSerializerMixin, serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    user = UserSerializer(read_only=True)
    topic = CommentTopicSerializer()

    class Meta:
        model = Comment
        fields = "__all__"


class CommentCreateUpdateSerializer(
    FieldPermissionsSerializerMixin, serializers.ModelSerializer
):
    id = serializers.ReadOnlyField()
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    topic = InstanceDictPrimaryKeyRelatedField(
        instance_class=CommentTopic,
        queryset=CommentTopic.objects.all(),
        related_serializer=CommentTopicSerializer,
    )

    class Meta:
        model = Comment
        fields = "__all__"
