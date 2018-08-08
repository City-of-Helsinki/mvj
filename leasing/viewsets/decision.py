from leasing.filters import DecisionFilter
from leasing.models import Decision
from leasing.serializers.decision import DecisionCreateUpdateSerializer, DecisionSerializer

from .utils import AtomicTransactionModelViewSet, AuditLogMixin


class DecisionViewSet(AuditLogMixin, AtomicTransactionModelViewSet):
    queryset = Decision.objects.all()
    serializer_class = DecisionSerializer
    filterset_class = DecisionFilter

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return DecisionCreateUpdateSerializer

        return DecisionSerializer
