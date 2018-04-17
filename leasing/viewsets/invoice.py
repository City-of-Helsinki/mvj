from rest_framework import viewsets

from leasing.models import Invoice
from leasing.serializers.invoice import InvoiceSerializer


class InvoiceViewSet(viewsets.ModelViewSet):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
