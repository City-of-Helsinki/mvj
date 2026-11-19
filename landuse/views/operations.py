from typing import Any

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from landuse.models.invoice import (
    INVOICE_STATUSES_BEFORE_SAP_EXPORT,
    Invoice,
    LandUseInvoiceExportError,
)
from landuse.models.payment_schedule import PaymentSchedule
from landuse.sap_export import LanduseSapExportDisabledError
from landuse.serializers.agreement import (
    InvoiceSerializer,
    PaymentScheduleRejectionSerializer,
    PaymentScheduleSerializer,
)
from landuse.views.mixins import LandUseApiEnabledFlagMixin, LandUsePaginationMixin


class PaymentSchedulePermission(BasePermission):
    message = _(
        "You do not have permission to perform this payment schedule operation."
    )

    def has_permission(self, request: Request, view: Any) -> bool:
        permission = {
            "list": "landuse.view_tab_payment_schedules",
            "retrieve": "landuse.view_tab_payment_schedules",
            "submit": "landuse.change_tab_payment_schedules",
            "return_to_draft": "landuse.change_tab_payment_schedules",
            "approve": "landuse.approve_paymentschedule",
            "reject": "landuse.approve_paymentschedule",
        }.get(view.action)
        return permission is not None and request.user.has_perm(permission)


class InvoicePermission(BasePermission):
    message = _("You do not have permission to perform this invoice operation.")

    def has_permission(self, request: Request, view: Any) -> bool:
        permission = {
            "list": "landuse.view_tab_invoices",
            "retrieve": "landuse.view_tab_invoices",
            "send_to_sap": "landuse.send_invoice_to_sap",
        }.get(view.action)
        return permission is not None and request.user.has_perm(permission)


class PaymentScheduleViewSet(
    LandUseApiEnabledFlagMixin,
    LandUsePaginationMixin,
    viewsets.ReadOnlyModelViewSet[PaymentSchedule],
):
    queryset = PaymentSchedule.objects.select_related(
        "agreement", "recipient_party", "contract"
    ).prefetch_related(
        "installments__items",
        "installments__invoice__recipient_snapshot",
        "installments__invoice__items",
        "installments__invoice__payments",
    )
    serializer_class = PaymentScheduleSerializer
    permission_classes = (IsAuthenticated, PaymentSchedulePermission)

    @action(detail=True, methods=("post",))
    def submit(self, request: Request, pk: str | None = None) -> Response:
        return self._transition(pk, "submit")

    @action(detail=True, methods=("post",))
    def approve(self, request: Request, pk: str | None = None) -> Response:
        return self._transition(pk, "approve")

    @action(detail=True, methods=("post",), url_path="return-to-draft")
    def return_to_draft(self, request: Request, pk: str | None = None) -> Response:
        return self._transition(pk, "return_to_draft")

    @action(detail=True, methods=("post",))
    def reject(self, request: Request, pk: str | None = None) -> Response:
        serializer = PaymentScheduleRejectionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return self._transition(pk, "reject", serializer.validated_data["reason"])

    @transaction.atomic
    def _transition(self, pk: str | None, operation: str, *args: str) -> Response:
        # Locks schedules for atomic update
        schedule = self.get_queryset().select_for_update().get(pk=self.get_object().pk)
        self._validate_schedules_invoices_statuses(schedule, operation)
        try:
            getattr(schedule, operation)(*args)
        except DjangoValidationError as error:
            raise ValidationError(
                error.message_dict if hasattr(error, "message_dict") else error.messages
            )
        return Response(
            PaymentScheduleSerializer(self.get_queryset().get(pk=schedule.pk)).data
        )

    def _validate_schedules_invoices_statuses(
        self, schedule: PaymentSchedule, operation: str
    ) -> None:
        # Locks installments for atomic update
        installment_count = len(
            list(schedule.installments.select_for_update().values_list("pk", flat=True))
        )
        # Locks invoices for atomic update
        invoices = list(
            Invoice.objects.select_for_update().filter(
                source_payment_schedule_installment__payment_schedule=schedule
            )
        )
        if (
            installment_count > 0
            and len(invoices) == installment_count
            and all(
                invoice.sent_at is not None
                or invoice.status not in INVOICE_STATUSES_BEFORE_SAP_EXPORT
                for invoice in invoices
            )
        ):
            raise ValidationError(
                {
                    "detail": _(
                        "Unable to do {} for this schedule. "
                        "All invoices for this payment schedule have already been sent to SAP."
                    ).format(operation)
                }
            )


class InvoiceViewSet(
    LandUseApiEnabledFlagMixin,
    LandUsePaginationMixin,
    viewsets.ReadOnlyModelViewSet[Invoice],
):
    queryset = Invoice.objects.select_related(
        "agreement", "recipient_party", "recipient_snapshot"
    ).prefetch_related("items", "payments")
    serializer_class = InvoiceSerializer
    permission_classes = (IsAuthenticated, InvoicePermission)

    @action(detail=True, methods=("post",), url_path="send-to-sap")
    @transaction.atomic
    def send_to_sap(self, request: Request, pk: str | None = None) -> Response:
        invoice = self.get_object()
        invoice = Invoice.objects.select_for_update().get(pk=invoice.pk)
        try:
            invoice.send_to_sap()
        except (LandUseInvoiceExportError, LanduseSapExportDisabledError) as error:
            raise ValidationError({"detail": str(error)})
        return Response(InvoiceSerializer(invoice).data, status=status.HTTP_200_OK)
