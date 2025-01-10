from field_permissions.viewsets import FieldPermissionsViewsetMixin
from leasing.models import InspectionAttachment
from leasing.serializers.inspection import (
    InspectionAttachmentCreateUpdateSerializer,
    InspectionAttachmentSerializer,
)
from utils.viewsets.mixins import FileMixin

from .utils import AtomicTransactionModelViewSet, MultiPartJsonParser


class InspectionAttachmentViewSet(
    FileMixin,
    FieldPermissionsViewsetMixin,
    AtomicTransactionModelViewSet,
):
    queryset = InspectionAttachment.objects.all()
    serializer_class = InspectionAttachmentSerializer
    parser_classes = (MultiPartJsonParser,)

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update", "metadata"):
            return InspectionAttachmentCreateUpdateSerializer

        return InspectionAttachmentSerializer
