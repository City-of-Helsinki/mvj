from rest_framework import viewsets

from leasing.filters import InvoiceFilter
from leasing.models import Invoice
from leasing.serializers.invoice import InvoiceCreateSerializer, InvoiceSerializer, InvoiceUpdateSerializer


class InvoiceViewSet(viewsets.ModelViewSet):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    filter_class = InvoiceFilter

    def get_serializer_class(self):
        if self.action == 'create':
            return InvoiceCreateSerializer

        if self.action in ('update', 'partial_update', 'metadata'):
            return InvoiceUpdateSerializer

        return InvoiceSerializer
