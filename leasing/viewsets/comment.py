from rest_framework import viewsets

from leasing.filters import CommentFilter
from leasing.models import Comment
from leasing.serializers.comment import CommentSerializer, CommentTopic, CommentTopicSerializer
from leasing.viewsets.utils import AuditLogMixin


class CommentViewSet(AuditLogMixin, viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    filter_class = CommentFilter


class CommentTopicViewSet(AuditLogMixin, viewsets.ModelViewSet):
    queryset = CommentTopic.objects.all()
    serializer_class = CommentTopicSerializer
