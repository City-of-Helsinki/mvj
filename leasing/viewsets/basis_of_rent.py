from leasing.models import BasisOfRent
from leasing.serializers.basis_of_rent import BasisOfRentCreateUpdateSerializer, BasisOfRentSerializer

from .utils import AtomicTransactionModelViewSet, AuditLogMixin


class BasisOfRentViewSet(AuditLogMixin, AtomicTransactionModelViewSet):
    queryset = BasisOfRent.objects.all()
    serializer_class = BasisOfRentSerializer

    def get_queryset(self):
        queryset = BasisOfRent.objects.select_related('plot_type', 'management', 'financing', 'index').prefetch_related(
            'rent_rates', 'property_identifiers', 'decisions', 'decisions__decision_maker')

        return queryset

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update', 'metadata'):
            return BasisOfRentCreateUpdateSerializer

        return BasisOfRentSerializer
