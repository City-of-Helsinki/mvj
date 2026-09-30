from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from landuse.models.invoice import Invoice, LandUseInvoiceExportError
from landuse.models.payment_schedule import PaymentSchedule
from landuse.sap_export import LanduseSapExportDisabledError
from landuse.serializers.agreement import (
    InvoiceSerializer,
    PaymentScheduleRejectionSerializer,
    PaymentScheduleSerializer,
)
from landuse.views.mixins import LandUseApiEnabledFlagMixin


class PaymentSchedulePermission(permissions.BasePermission):
    message = "You do not have permission to perform this payment schedule operation."

    # TODO: define permissions
    # def has_permission(self, request, view):
    #     permission = {
    #         "submit": "landuse.change_paymentschedule",
    #         "approve": "landuse.approve_paymentschedule",
    #         "reject": "landuse.approve_paymentschedule",
    #     }.get(view.action, "landuse.view_paymentschedule")
    #     return request.user.has_perm(permission)


class InvoicePermission(permissions.BasePermission):
    message = "You do not have permission to perform this invoice operation."

    # TODO: define permissions
    # def has_permission(self, request, view):
    #     permission = {
    #         "send_to_sap": "landuse.send_invoice_to_sap",
    #     }.get(view.action, "landuse.view_invoice")
    #     return request.user.has_perm(permission)


class PaymentScheduleViewSet(LandUseApiEnabledFlagMixin, viewsets.ReadOnlyModelViewSet):
    queryset = PaymentSchedule.objects.select_related(
        "agreement", "recipient_party", "contract"
    ).prefetch_related("installments__items")
    serializer_class = PaymentScheduleSerializer
    # TODO: define permissions
    # permission_classes = (permissions.IsAuthenticated, PaymentSchedulePermission)

    @action(detail=True, methods=("post",))
    def submit(self, request, pk=None):
        return self._transition(pk, "submit")

    @action(detail=True, methods=("post",))
    def approve(self, request, pk=None):
        return self._transition(pk, "approve")

    @action(detail=True, methods=("post",))
    def reject(self, request, pk=None):
        serializer = PaymentScheduleRejectionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return self._transition(pk, "reject", serializer.validated_data["reason"])

    @transaction.atomic
    def _transition(self, pk, operation, *args):
        schedule = self.get_object()
        schedule = self.get_queryset().select_for_update().get(pk=schedule.pk)
        try:
            getattr(schedule, operation)(*args)
        except DjangoValidationError as error:
            raise ValidationError(
                error.message_dict if hasattr(error, "message_dict") else error.messages
            )
        return Response(PaymentScheduleSerializer(schedule).data)


class InvoiceViewSet(LandUseApiEnabledFlagMixin, viewsets.ReadOnlyModelViewSet):
    queryset = Invoice.objects.select_related(
        "agreement", "recipient_party", "recipient_snapshot"
    ).prefetch_related("items", "payments")
    serializer_class = InvoiceSerializer
    # TODO: define permissions
    # permission_classes = (permissions.IsAuthenticated, InvoicePermission)

    @action(detail=True, methods=("post",), url_path="send-to-sap")
    @transaction.atomic
    def send_to_sap(self, request, pk=None):
        invoice = self.get_object()
        invoice = Invoice.objects.select_for_update().get(pk=invoice.pk)
        try:
            invoice.send_to_sap()
        except (LandUseInvoiceExportError, LanduseSapExportDisabledError) as error:
            raise ValidationError({"detail": str(error)})
        return Response(InvoiceSerializer(invoice).data, status=status.HTTP_200_OK)
