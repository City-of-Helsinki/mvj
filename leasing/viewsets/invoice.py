from rest_framework.viewsets import ReadOnlyModelViewSet

from leasing.filters import InvoiceFilter, InvoiceSetFilter
from leasing.models import Invoice
from leasing.models.invoice import InvoiceSet
from leasing.serializers.invoice import (
    InvoiceCreateSerializer, InvoiceSerializer, InvoiceSetSerializer, InvoiceUpdateSerializer)

from .utils import AtomicTransactionModelViewSet


class InvoiceViewSet(AtomicTransactionModelViewSet):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    filter_class = InvoiceFilter

    def get_queryset(self):
        queryset = Invoice.objects.select_related('recipient').prefetch_related(
            'rows__receivable_type', 'rows', 'rows__tenant', 'rows__tenant__tenantcontact_set',
            'rows__tenant__tenantcontact_set__contact', 'payments')

        return queryset

    def get_serializer_class(self):
        if self.action == 'create':
            return InvoiceCreateSerializer

        if self.action in ('update', 'partial_update', 'metadata'):
            return InvoiceUpdateSerializer

        return InvoiceSerializer


class InvoiceSetViewSet(ReadOnlyModelViewSet):
    queryset = InvoiceSet.objects.all()
    serializer_class = InvoiceSetSerializer
    filter_class = InvoiceSetFilter
