from rest_framework.decorators import action

from field_permissions.viewsets import FieldPermissionsViewsetMixin
from file_operations.viewsets.mixins import FileMixin
from leasing.models import InspectionAttachment
from leasing.serializers.inspection import (
    InspectionAttachmentCreateUpdateSerializer,
    InspectionAttachmentSerializer,
)

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

    @action(methods=["get"], detail=True)
    def download(self, request, pk=None):
        """Needed to inform FileDownloadMixin of which field holds the file."""
        return super().download(request, pk, file_field="file")
