from leasing.filters import InvoiceFilter
from leasing.models import Invoice
from leasing.serializers.invoice import InvoiceCreateSerializer, InvoiceSerializer, InvoiceUpdateSerializer

from .utils import AtomicTransactionModelViewSet


class InvoiceViewSet(AtomicTransactionModelViewSet):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    filter_class = InvoiceFilter

    def get_queryset(self):
        queryset = Invoice.objects.select_related('recipient').prefetch_related(
            'rows', 'rows__tenant', 'rows__tenant__tenantcontact_set', 'rows__tenant__tenantcontact_set__contact')

        return queryset

    def get_serializer_class(self):
        if self.action == 'create':
            return InvoiceCreateSerializer

        if self.action in ('update', 'partial_update', 'metadata'):
            return InvoiceUpdateSerializer

        return InvoiceSerializer
