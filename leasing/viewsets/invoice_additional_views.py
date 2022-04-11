import datetime
from decimal import Decimal, InvalidOperation

from dateutil import parser
from django.utils.translation import gettext_lazy as _
from paramiko import SSHException
from pysftp import ConnectionException, CredentialException, HostKeysException
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from laske_export.exporter import LaskeExporter, LaskeExporterError
from leasing.models import Invoice, ReceivableType
from leasing.models.invoice import InvoiceRow, InvoiceSet
from leasing.permissions import PerMethodPermission
from leasing.serializers.invoice import InvoiceSerializer, InvoiceSetSerializer


def get_values_from_credit_request(data):
    amount = data.get("amount", None)
    receivable_type_id = data.get("receivable_type")
    notes = data.get("notes", "")
    receivable_type = None

    if amount is not None and not receivable_type_id:
        raise ValidationError("receivable_type is required if amount is provided.")

    if amount is not None:
        try:
            amount = Decimal(amount)
        except InvalidOperation:
            raise ValidationError(_("Invalid amount"))

        if amount.compare(Decimal(0)) != Decimal(1):
            raise ValidationError(_("Amount must be bigger than zero"))

    if receivable_type_id:
        try:
            receivable_type = ReceivableType.objects.get(pk=receivable_type_id)
        except ReceivableType.DoesNotExist:
            raise ValidationError(
                'Receivable_type "{}" not found'.format(receivable_type_id)
            )

    return amount, receivable_type, notes


def get_object_from_query_params(object_type, query_params):
    assert object_type in ["invoice", "invoice_row", "invoice_set"]

    object_type_map = {
        "invoice": {"name": "Invoice", "class": Invoice, "param_name": "invoice"},
        "invoice_row": {
            "name": "Invoice",
            "class": InvoiceRow,
            "param_name": "invoice_row",
        },
        "invoice_set": {
            "name": "Invoice",
            "class": InvoiceSet,
            "param_name": "invoice_set",
        },
    }

    if not query_params.get(object_type_map[object_type]["param_name"]):
        raise ValidationError(
            "{} parameter is mandatory".format(
                object_type_map[object_type]["param_name"]
            )
        )

    try:

        return object_type_map[object_type]["class"].objects.get(
            pk=int(query_params.get(object_type_map[object_type]["param_name"]))
        )
    except Invoice.DoesNotExist:
        raise ValidationError(
            "{} does not exist".format(object_type_map[object_type]["name"])
        )
    except ValueError:
        raise ValidationError(
            "Invalid {} id".format(object_type_map[object_type]["name"])
        )


class InvoiceCalculatePenaltyInterestView(APIView):
    permission_classes = (PerMethodPermission,)
    perms_map = {"GET": ["leasing.add_collectionletter"]}

    def get_view_name(self):
        return _("Calculate penalty interest")

    def get_view_description(self, html=False):
        return _("Calculate penalty interest for the outstanding amount until today")

    def get(self, request, format=None):
        invoice = get_object_from_query_params("invoice", request.query_params)

        end_date = datetime.date.today()
        if request.query_params.get("end_date"):
            end_date = parser.parse(request.query_params["end_date"]).date()

        return Response(invoice.calculate_penalty_interest(calculation_date=end_date))


class InvoiceCreditView(APIView):
    permission_classes = (PerMethodPermission,)
    perms_map = {"POST": ["leasing.add_invoice"]}

    def get_view_name(self):
        return _("Credit invoice")

    def get_view_description(self, html=False):
        return _("Credit invoice or part of it")

    def post(self, request, format=None):
        invoice = get_object_from_query_params("invoice", request.query_params)

        if not invoice.sent_to_sap_at:
            raise ValidationError(
                _("Cannot credit invoices that have not been sent to SAP")
            )

        amount, receivable_type, notes = get_values_from_credit_request(request.data)

        try:
            credit_invoice = invoice.create_credit_invoice(
                amount=amount, receivable_type=receivable_type, notes=notes
            )
        except RuntimeError as e:
            raise APIException(str(e))

        credit_invoice_serializer = InvoiceSerializer(credit_invoice)

        result = {"invoice": credit_invoice_serializer.data}

        return Response(result)


class InvoiceRowCreditView(APIView):
    permission_classes = (PerMethodPermission,)
    perms_map = {"POST": ["leasing.add_invoice"]}

    def get_view_name(self):
        return _("Credit invoice row")

    def get_view_description(self, html=False):
        return _("Credit invoice row or part of it")

    def post(self, request, format=None):
        invoice_row = get_object_from_query_params("invoice_row", request.query_params)

        amount = request.data.get("amount", None)

        if amount is not None:
            try:
                amount = Decimal(amount)
            except InvalidOperation:
                raise ValidationError(_("Invalid amount"))

            if amount.compare(Decimal(0)) != Decimal(1):
                raise ValidationError(_("Amount must be bigger than zero"))

        try:
            credit_invoice = invoice_row.invoice.create_credit_invoice(
                row_ids=[invoice_row.id], amount=amount
            )
        except RuntimeError as e:
            raise APIException(str(e))

        credit_invoice_serializer = InvoiceSerializer(credit_invoice)

        result = {"invoice": credit_invoice_serializer.data}

        return Response(result)


class InvoiceSetCreditView(APIView):
    permission_classes = (PerMethodPermission,)
    perms_map = {"POST": ["leasing.add_invoice"]}

    def get_view_name(self):
        return _("Credit invoice row")

    def get_view_description(self, html=False):
        return _("Credit invoice row or part of it")

    def post(self, request, format=None):
        invoiceset = get_object_from_query_params("invoice_set", request.query_params)

        amount, receivable_type, notes = get_values_from_credit_request(request.data)

        try:
            if amount and receivable_type:
                credit_invoiceset = invoiceset.create_credit_invoiceset_for_amount(
                    amount=amount, receivable_type=receivable_type, notes=notes
                )
            else:
                credit_invoiceset = invoiceset.create_credit_invoiceset(
                    receivable_type=receivable_type, notes=notes
                )
        except RuntimeError as e:
            raise APIException(str(e))

        credit_invoiceset_serializer = InvoiceSetSerializer(credit_invoiceset)

        result = {"invoiceset": credit_invoiceset_serializer.data, "invoices": []}

        for credit_invoice in credit_invoiceset.invoices.all():
            result["invoices"].append(InvoiceSerializer(credit_invoice).data)

        return Response(result)


class InvoiceExportToLaskeView(APIView):
    permission_classes = (PerMethodPermission,)
    perms_map = {"POST": ["leasing.add_invoice"]}

    def get_view_name(self):
        return _("Export invoice to Laske")

    def get_view_description(self, html=False):
        return _("Export chosen invoice to Laske SAP system")

    def post(self, request, format=None):
        invoice = get_object_from_query_params("invoice", request.query_params)
        if invoice.sent_to_sap_at:
            raise ValidationError(_("This invoice has already been sent to SAP"))

        if invoice.number:
            raise ValidationError(
                _("Can't send invoices that already have a number to SAP")
            )

        try:
            exporter = LaskeExporter(service_unit=invoice.service_unit)
            exporter.export_invoices(invoice)
        except (
            LaskeExporterError,
            ConnectionException,
            CredentialException,
            SSHException,
            HostKeysException,
        ) as e:
            raise APIException(str(e))

        return Response({"success": True})
