from rest_framework import viewsets

from leasing.models import AreaNote
from leasing.serializers.area_note import AreaNoteCreateUpdateSerializer, AreaNoteSerializer
from leasing.viewsets.utils import AuditLogMixin


class AreaNoteViewSet(AuditLogMixin, viewsets.ModelViewSet):
    queryset = AreaNote.objects.all()
    serializer_class = AreaNoteSerializer

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update', 'metadata'):
            return AreaNoteCreateUpdateSerializer

        return AreaNoteSerializer
