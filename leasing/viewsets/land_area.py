from field_permissions.viewsets import FieldPermissionsViewsetMixin
from leasing.models import LeaseAreaAttachment
from leasing.serializers.land_area import (
    LeaseAreaAttachmentCreateUpdateSerializer,
    LeaseAreaAttachmentSerializer,
)

from .utils import (
    AtomicTransactionModelViewSet,
    AuditLogMixin,
    FileMixin,
    MultiPartJsonParser,
)


class LeaseAreaAttachmentViewSet(
    FileMixin,
    AuditLogMixin,
    FieldPermissionsViewsetMixin,
    AtomicTransactionModelViewSet,
):
    queryset = LeaseAreaAttachment.objects.all()
    serializer_class = LeaseAreaAttachmentSerializer
    parser_classes = (MultiPartJsonParser,)

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update", "metadata"):
            return LeaseAreaAttachmentCreateUpdateSerializer

        return LeaseAreaAttachmentSerializer
