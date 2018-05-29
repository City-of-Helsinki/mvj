from rest_framework import serializers

from users.serializers import UserSerializer

from ..models import Comment, CommentTopic
from .utils import InstanceDictPrimaryKeyRelatedField


class CommentTopicSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()

    class Meta:
        model = CommentTopic
        fields = '__all__'


class CommentSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    user = UserSerializer(read_only=True)
    topic = InstanceDictPrimaryKeyRelatedField(instance_class=CommentTopic, queryset=CommentTopic.objects.all(),
                                               related_serializer=CommentTopicSerializer)

    class Meta:
        model = Comment
        fields = '__all__'


class CommentCreateUpdateSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    topic = InstanceDictPrimaryKeyRelatedField(instance_class=CommentTopic, queryset=CommentTopic.objects.all(),
                                               related_serializer=CommentTopicSerializer)

    class Meta:
        model = Comment
        fields = '__all__'
