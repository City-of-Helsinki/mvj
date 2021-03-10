from decimal import Decimal, InvalidOperation

from django.utils.translation import ugettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend
from django_filters.widgets import BooleanWidget
from paramiko import SSHException
from pysftp import ConnectionException, CredentialException, HostKeysException
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework_gis.filters import InBBoxFilter

from field_permissions.viewsets import FieldPermissionsViewsetMixin
from laske_export.exporter import LaskeExporter, LaskeExporterException
from leasing.enums import InvoiceState, InvoiceType
from leasing.filters import (
    CoalesceOrderingFilter,
    LandUseAgreementInvoiceFilter,
    LandUseAgreementInvoiceRowFilter,
)
from leasing.models import ReceivableType
from leasing.models.land_use_agreement import (
    LandUseAgreement,
    LandUseAgreementAttachment,
    LandUseAgreementInvoice,
    LandUseAgreementInvoiceRow,
    LandUseAgreementInvoiceSet,
)
from leasing.permissions import PerMethodPermission
from leasing.serializers.invoice import ReceivableTypeSerializer
from leasing.serializers.land_use_agreement import (
    LandUseAgreementAttachmentCreateUpdateSerializer,
    LandUseAgreementAttachmentSerializer,
    LandUseAgreementCreateSerializer,
    LandUseAgreementCreditNoteUpdateSerializer,
    LandUseAgreementInvoiceCreateSerializer,
    LandUseAgreementInvoiceRowSerializer,
    LandUseAgreementInvoiceSerializer,
    LandUseAgreementInvoiceSerializerWithSuccinctLease,
    LandUseAgreementInvoiceSetSerializer,
    LandUseAgreementInvoiceUpdateSerializer,
    LandUseAgreementListSerializer,
    LandUseAgreementRetrieveSerializer,
    LandUseAgreementUpdateSerializer,
    SentToSapLandUseAgreementInvoiceUpdateSerializer,
)

from .utils import (
    AtomicTransactionModelViewSet,
    AuditLogMixin,
    FileMixin,
    MultiPartJsonParser,
)


def get_object_from_query_params(object_type, query_params):
    assert object_type in [
        "land_use_agreement_invoice",
        "land_use_agreement_invoice_row",
        "land_use_agreement_invoice_set",
    ]

    object_type_map = {
        "land_use_agreement_invoice": {
            "name": "LandUseAgreementInvoice",
            "class": LandUseAgreementInvoice,
            "param_name": "invoice",
        },
        "land_use_agreement_invoice_row": {
            "name": "LandUseAgreementInvoice",
            "class": LandUseAgreementInvoiceRow,
            "param_name": "invoice_row",
        },
        "land_use_agreement_invoice_set": {
            "name": "LandUseAgreementInvoice",
            "class": LandUseAgreementInvoiceSet,
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
    except LandUseAgreementInvoice.DoesNotExist:
        raise ValidationError(
            "{} does not exist".format(object_type_map[object_type]["name"])
        )
    except ValueError:
        raise ValidationError(
            "Invalid {} id".format(object_type_map[object_type]["name"])
        )


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


class LandUseAgreementViewSet(
    AuditLogMixin, FieldPermissionsViewsetMixin, AtomicTransactionModelViewSet
):
    queryset = LandUseAgreement.objects.all()
    serializer_class = LandUseAgreementRetrieveSerializer
    filter_backends = (
        DjangoFilterBackend,
        OrderingFilter,
        InBBoxFilter,
        SearchFilter,
    )
    search_fields = [
        "^estate_ids__estate_id",
        "^identifier__identifier",
        "litigants__contacts__first_name",
        "litigants__contacts__last_name",
        "litigants__contacts__name",
        "^plan_number",
        "status__name",
    ]

    def get_serializer_class(self):
        if self.action in ("create", "metadata"):
            return LandUseAgreementCreateSerializer

        if self.action in ("update", "partial_update"):
            return LandUseAgreementUpdateSerializer

        if self.action == "list":
            return LandUseAgreementListSerializer

        return LandUseAgreementRetrieveSerializer


class LandUseAgreementAttachmentViewSet(
    FileMixin,
    AuditLogMixin,
    FieldPermissionsViewsetMixin,
    AtomicTransactionModelViewSet,
):
    queryset = LandUseAgreementAttachment.objects.all()
    serializer_class = LandUseAgreementAttachmentSerializer
    parser_classes = (MultiPartJsonParser,)

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update", "metadata"):
            return LandUseAgreementAttachmentCreateUpdateSerializer

        return LandUseAgreementAttachmentSerializer


class LandUseAgreementInvoiceViewSet(
    FieldPermissionsViewsetMixin, AtomicTransactionModelViewSet
):
    queryset = LandUseAgreementInvoice.objects.all()
    serializer_class = LandUseAgreementInvoiceSerializer
    filterset_class = LandUseAgreementInvoiceFilter
    filter_backends = (DjangoFilterBackend, CoalesceOrderingFilter)
    ordering_fields = (
        "sent_to_sap_at",
        "recipient_name",
        "number",
        "due_date",
        "total_amount",
        "billed_amount",
        "lease__identifier__type__identifier",
        "lease__identifier__municipality__identifier",
        "lease__identifier__district__identifier",
        "lease__identifier__sequence",
    )
    coalesce_ordering = {"recipient_name": ("recipient__name", "recipient__last_name")}

    def get_queryset(self):
        queryset = LandUseAgreementInvoice.objects.select_related(
            "recipient"
        ).prefetch_related(
            "rows__receivable_type",
            "rows",
            "rows__litigant",
            "rows__litigant__landuseagreementlitigantcontact_set",
            "rows__litigant__landuseagreementlitigantcontact_set__contact",
            "payments",
            "credit_invoices",
            "interest_invoices",
        )

        return queryset

    def get_serializer_class(self):
        if self.action == "create":
            return LandUseAgreementInvoiceCreateSerializer

        if self.action in ("update", "partial_update", "metadata"):
            if "pk" in self.kwargs:
                instance = self.get_object()
                if instance:
                    if instance.sent_to_sap_at:
                        return SentToSapLandUseAgreementInvoiceUpdateSerializer

                    if instance.type == InvoiceType.CREDIT_NOTE:
                        return LandUseAgreementCreditNoteUpdateSerializer

            return LandUseAgreementInvoiceUpdateSerializer

        if self.request.query_params.get("going_to_sap"):
            boolean_widget = BooleanWidget()
            # check passed value against widget's truthy values
            if boolean_widget.value_from_datadict(
                self.request.query_params, None, "going_to_sap"
            ):
                return LandUseAgreementInvoiceSerializerWithSuccinctLease

        return LandUseAgreementInvoiceSerializer

    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        if (
            instance.sent_to_sap_at
            and self.get_serializer_class()
            is not SentToSapLandUseAgreementInvoiceUpdateSerializer
        ):
            raise ValidationError(_("Can't edit invoices that have been sent to SAP"))

        if instance.state == InvoiceState.REFUNDED:
            raise ValidationError(_("Can't edit fully refunded invoices"))

        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        if instance.number:
            raise ValidationError(_("Can't delete numbered invoices"))

        if instance.sent_to_sap_at:
            raise ValidationError(_("Can't delete invoices that have been sent to SAP"))

        return super().destroy(request, *args, **kwargs)


class LandUseAgreementInvoiceRowViewSet(
    FieldPermissionsViewsetMixin, ReadOnlyModelViewSet
):
    queryset = LandUseAgreementInvoiceRow.objects.all()
    serializer_class = LandUseAgreementInvoiceRowSerializer
    filterset_class = LandUseAgreementInvoiceRowFilter


class LandUseAgreementReceivableTypeViewSet(ReadOnlyModelViewSet):
    queryset = ReceivableType.objects.all()
    serializer_class = ReceivableTypeSerializer


class LandUseAgreementInvoiceCreditView(APIView):
    permission_classes = (PerMethodPermission,)
    perms_map = {"POST": ["land_use_agreement.add_invoice"]}

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

        credit_invoice_serializer = LandUseAgreementInvoiceSerializer(credit_invoice)

        result = {"invoice": credit_invoice_serializer.data}

        return Response(result)


class LandUseAgreementInvoiceRowCreditView(APIView):
    permission_classes = (PerMethodPermission,)
    perms_map = {"POST": ["land_use_agreement.add_invoice"]}

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

        credit_invoice_serializer = LandUseAgreementInvoiceSerializer(credit_invoice)

        result = {"invoice": credit_invoice_serializer.data}

        return Response(result)


class LandUseAgreementInvoiceSetCreditView(APIView):
    permission_classes = (PerMethodPermission,)
    perms_map = {"POST": ["land_use_agreement.add_invoice"]}

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

        credit_invoiceset_serializer = LandUseAgreementInvoiceSetSerializer(
            credit_invoiceset
        )

        result = {"invoiceset": credit_invoiceset_serializer.data, "invoices": []}

        for credit_invoice in credit_invoiceset.invoices.all():
            result["invoices"].append(
                LandUseAgreementInvoiceSerializer(credit_invoice).data
            )

        return Response(result)


class LandUseAgreementInvoiceExportToLaskeView(APIView):
    permission_classes = (PerMethodPermission,)
    perms_map = {"POST": ["land_use_agreement.add_invoice"]}

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
            exporter = LaskeExporter()
            exporter.export_invoices(invoice)
        except (
            LaskeExporterException,
            ConnectionException,
            CredentialException,
            SSHException,
            HostKeysException,
        ) as e:
            raise APIException(str(e))

        return Response({"success": True})
