from django.utils.translation import ugettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend
from django_filters.widgets import BooleanWidget
from rest_framework.exceptions import ValidationError
from rest_framework.filters import OrderingFilter
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework_gis.filters import InBBoxFilter

from field_permissions.viewsets import FieldPermissionsViewsetMixin
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
)
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


class LandUseAgreementViewSet(
    AuditLogMixin, FieldPermissionsViewsetMixin, AtomicTransactionModelViewSet
):
    queryset = LandUseAgreement.objects.all()
    serializer_class = LandUseAgreementRetrieveSerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter, InBBoxFilter)

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
            "rows__tenant",
            "rows__tenant__tenantcontact_set",
            "rows__tenant__tenantcontact_set__contact",
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
