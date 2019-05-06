from field_permissions.viewsets import FieldPermissionsViewsetMixin
from leasing.models import InspectionAttachment
from leasing.serializers.inspection import InspectionAttachmentCreateUpdateSerializer, InspectionAttachmentSerializer

from .utils import AtomicTransactionModelViewSet, AuditLogMixin, FileMixin, MultiPartJsonParser


class InspectionAttachmentViewSet(FileMixin, AuditLogMixin, FieldPermissionsViewsetMixin,
                                  AtomicTransactionModelViewSet):
    queryset = InspectionAttachment.objects.all()
    serializer_class = InspectionAttachmentSerializer
    parser_classes = (MultiPartJsonParser,)

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update', 'metadata'):
            return InspectionAttachmentCreateUpdateSerializer

        return InspectionAttachmentSerializer
