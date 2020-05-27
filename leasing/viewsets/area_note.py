from rest_framework import filters

from field_permissions.viewsets import FieldPermissionsViewsetMixin
from leasing.models import AreaNote
from leasing.serializers.area_note import (
    AreaNoteCreateUpdateSerializer,
    AreaNoteSerializer,
)

from .utils import AtomicTransactionModelViewSet, AuditLogMixin


class AreaNoteViewSet(
    AuditLogMixin, FieldPermissionsViewsetMixin, AtomicTransactionModelViewSet
):
    queryset = AreaNote.objects.all()
    serializer_class = AreaNoteSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ("note",)

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update", "metadata"):
            return AreaNoteCreateUpdateSerializer

        return AreaNoteSerializer
