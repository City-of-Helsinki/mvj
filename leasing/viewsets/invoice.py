from django.utils.translation import ugettext_lazy as _
from rest_framework.exceptions import APIException
from rest_framework.viewsets import ReadOnlyModelViewSet

from field_permissions.viewsets import FieldPermissionsViewsetMixin
from leasing.enums import InvoiceState, InvoiceType
from leasing.filters import InvoiceFilter, InvoiceRowFilter, InvoiceSetFilter
from leasing.models import Invoice
from leasing.models.invoice import InvoiceRow, InvoiceSet
from leasing.serializers.invoice import (
    CreditNoteUpdateSerializer, InvoiceCreateSerializer, InvoiceRowSerializer, InvoiceSerializer, InvoiceSetSerializer,
    InvoiceUpdateSerializer)

from .utils import AtomicTransactionModelViewSet


class InvoiceViewSet(FieldPermissionsViewsetMixin, AtomicTransactionModelViewSet):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    filterset_class = InvoiceFilter

    def get_queryset(self):
        queryset = Invoice.objects.select_related('recipient').prefetch_related(
            'rows__receivable_type', 'rows', 'rows__tenant', 'rows__tenant__tenantcontact_set',
            'rows__tenant__tenantcontact_set__contact', 'payments', 'credit_invoices')

        return queryset

    def get_serializer_class(self):
        if self.action == 'create':
            return InvoiceCreateSerializer

        if self.action in ('update', 'partial_update', 'metadata'):
            if 'pk' in self.kwargs:
                instance = self.get_object()
                if instance:
                    if instance.type == InvoiceType.CREDIT_NOTE:
                        return CreditNoteUpdateSerializer

            return InvoiceUpdateSerializer

        return InvoiceSerializer

    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        if instance.state == InvoiceState.REFUNDED:
            raise APIException(_("Can't edit fully refunded invoices"))

        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        if instance.number:
            raise APIException(_("Can't delete numbered invoices"))

        if instance.sent_to_sap_at:
            raise APIException(_("Can't delete invoices that have been sent to SAP"))

        return super().destroy(request, *args, **kwargs)


class InvoiceRowViewSet(FieldPermissionsViewsetMixin, ReadOnlyModelViewSet):
    queryset = InvoiceRow.objects.all()
    serializer_class = InvoiceRowSerializer
    filterset_class = InvoiceRowFilter


class InvoiceSetViewSet(ReadOnlyModelViewSet):
    queryset = InvoiceSet.objects.all()
    serializer_class = InvoiceSetSerializer
    filterset_class = InvoiceSetFilter
