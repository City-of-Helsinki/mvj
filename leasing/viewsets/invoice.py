from decimal import Decimal

from rest_framework.decorators import action
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from leasing.filters import InvoiceFilter, InvoiceRowFilter, InvoiceSetFilter
from leasing.models import Invoice
from leasing.models.invoice import InvoiceRow, InvoiceSet, ReceivableType
from leasing.serializers.invoice import (
    InvoiceCreateSerializer, InvoiceRowSerializer, InvoiceSerializer, InvoiceSetSerializer, InvoiceUpdateSerializer)

from .utils import AtomicTransactionModelViewSet


def get_amount_and_receivable_type(data):
    amount = data.get('amount')
    receivable_type_id = data.get('receivable_type')
    receivable_type = None

    if amount and not receivable_type_id:
        raise APIException('receivable_type is required if amount is provided.')

    if amount:
        amount = Decimal(amount)

        if amount <= 0:
            raise APIException('Amount must be bigger than zero')

    if receivable_type_id:
        try:
            receivable_type = ReceivableType.objects.get(pk=receivable_type_id)
        except ReceivableType.DoesNotExist:
            raise APIException('Receivable_type "{}" not found'.format(receivable_type_id))

    return amount, receivable_type


class InvoiceViewSet(AtomicTransactionModelViewSet):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    filterset_class = InvoiceFilter

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

    @action(methods=['post'], detail=True)
    def credit(self, request, pk=None):
        invoice = self.get_object()

        amount, receivable_type = get_amount_and_receivable_type(request.data)

        try:
            credit_invoice = invoice.create_credit_invoice(amount=amount, receivable_type=receivable_type)
        except RuntimeError as e:
            raise APIException(e)

        credit_invoice_serializer = InvoiceSerializer(credit_invoice)

        result = {
            'invoice': credit_invoice_serializer.data,
        }

        return Response(result)


class InvoiceRowViewSet(ReadOnlyModelViewSet):
    queryset = InvoiceRow.objects.all()
    serializer_class = InvoiceRowSerializer
    filterset_class = InvoiceRowFilter

    @action(methods=['post'], detail=True)
    def credit(self, request, pk=None):
        invoice_row = self.get_object()

        amount = request.data.get('amount')

        try:
            credit_invoice = invoice_row.invoice.create_credit_invoice(row_ids=[invoice_row.id], amount=amount)
        except RuntimeError as e:
            raise APIException(e)

        credit_invoice_serializer = InvoiceSerializer(credit_invoice)

        result = {
            'invoice': credit_invoice_serializer.data,
        }

        return Response(result)


class InvoiceSetViewSet(ReadOnlyModelViewSet):
    queryset = InvoiceSet.objects.all()
    serializer_class = InvoiceSetSerializer
    filterset_class = InvoiceSetFilter

    @action(methods=['post'], detail=True)
    def credit(self, request, pk=None):
        invoiceset = self.get_object()

        amount, receivable_type = get_amount_and_receivable_type(request.data)

        try:
            if amount and receivable_type:
                credit_invoiceset = invoiceset.create_credit_invoiceset_for_amount(
                    amount=amount, receivable_type=receivable_type)
            else:
                credit_invoiceset = invoiceset.create_credit_invoiceset(receivable_type=receivable_type)
        except RuntimeError as e:
            raise APIException(e)

        credit_invoiceset_serializer = InvoiceSetSerializer(credit_invoiceset)

        result = {
            'invoiceset': credit_invoiceset_serializer.data,
            'invoices': [],
        }

        for credit_invoice in credit_invoiceset.invoices.all():
            result['invoices'].append(InvoiceSerializer(credit_invoice).data)

        return Response(result)
