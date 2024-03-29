from field_permissions.viewsets import FieldPermissionsViewsetMixin
from leasing.filters import CommentFilter
from leasing.models import Comment
from leasing.serializers.comment import (
    CommentCreateUpdateSerializer,
    CommentSerializer,
    CommentTopic,
    CommentTopicSerializer,
)

from .utils import AtomicTransactionModelViewSet


class CommentViewSet(FieldPermissionsViewsetMixin, AtomicTransactionModelViewSet):
    queryset = Comment.objects.all().select_related("lease", "user", "topic")
    serializer_class = CommentSerializer
    filterset_class = CommentFilter

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update", "metadata"):
            return CommentCreateUpdateSerializer

        return CommentSerializer


class CommentTopicViewSet(FieldPermissionsViewsetMixin, AtomicTransactionModelViewSet):
    queryset = CommentTopic.objects.all()
    serializer_class = CommentTopicSerializer
