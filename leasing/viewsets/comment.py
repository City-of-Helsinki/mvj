from rest_framework import viewsets

from leasing.filters import CommentFilter
from leasing.models import Comment
from leasing.serializers.comment import (
    CommentCreateUpdateSerializer, CommentSerializer, CommentTopic, CommentTopicSerializer)
from leasing.viewsets.utils import AuditLogMixin


class CommentViewSet(AuditLogMixin, viewsets.ModelViewSet):
    queryset = Comment.objects.all().select_related('lease', 'user', 'topic')
    serializer_class = CommentSerializer
    filter_class = CommentFilter

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update', 'metadata'):
            return CommentCreateUpdateSerializer

        return CommentSerializer


class CommentTopicViewSet(AuditLogMixin, viewsets.ModelViewSet):
    queryset = CommentTopic.objects.all()
    serializer_class = CommentTopicSerializer
