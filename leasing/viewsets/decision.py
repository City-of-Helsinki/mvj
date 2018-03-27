from rest_framework import viewsets

from leasing.filters import DecisionFilter
from leasing.models import Decision
from leasing.serializers.decision import DecisionCreateUpdateSerializer, DecisionSerializer
from leasing.viewsets.utils import AuditLogMixin


class DecisionViewSet(AuditLogMixin, viewsets.ModelViewSet):
    queryset = Decision.objects.all()
    serializer_class = DecisionSerializer
    filter_class = DecisionFilter

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return DecisionCreateUpdateSerializer

        return DecisionSerializer
