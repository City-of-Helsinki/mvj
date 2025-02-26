from django import forms
from django.utils.translation import gettext_lazy as _
from rest_framework.request import Request
from rest_framework.response import Response

from leasing.models import ServiceUnit
from leasing.models.invoice import InvoicePayment
from leasing.report.excel import ExcelCell, ExcelRow, SumCell
from leasing.report.lease.common_getters import LeaseLinkData
from leasing.report.report_base import ReportBase


def get_invoice_number(obj):
    return obj.invoice.number


def get_lease_link_data_from_invoice_payment(
    invoice_payment: InvoicePayment,
) -> LeaseLinkData:
    return {
        "id": invoice_payment.invoice.lease.id,
        "identifier": invoice_payment.invoice.lease.get_identifier_string(),
    }


class InvoicePaymentsReport(ReportBase):
    name = _("Invoice payments")
    description = _(
        "Show all the payments that have been paid between the start and the end date"
    )
    slug = "invoice_payments"
    input_fields = {
        "service_unit": forms.ModelMultipleChoiceField(
            label=_("Service unit"),
            queryset=ServiceUnit.objects.all(),
            required=False,
        ),
        "start_date": forms.DateField(label=_("Start date"), required=True),
        "end_date": forms.DateField(label=_("End date"), required=True),
    }
    output_fields = {
        "invoice_number": {
            "source": get_invoice_number,
            "label": _("Invoice number"),
            "is_numeric": True,
        },
        "lease_link_data": {
            "source": get_lease_link_data_from_invoice_payment,
            "label": _("Lease id"),
        },
        "paid_date": {"label": _("Paid date"), "format": "date"},
        "paid_amount": {"label": _("Paid amount"), "format": "money", "width": 13},
        "filing_code": {"label": _("Filing code")},
    }

    def get_data(self, input_data):
        qs = (
            InvoicePayment.objects.filter(
                paid_date__gte=input_data["start_date"],
                paid_date__lte=input_data["end_date"],
            )
            .select_related(
                "invoice",
                "invoice__lease",
                "invoice__lease__identifier",
                "invoice__lease__identifier__type",
                "invoice__lease__identifier__district",
                "invoice__lease__identifier__municipality",
            )
            .order_by("paid_date")
        )

        if input_data["service_unit"]:
            qs = qs.filter(invoice__service_unit__in=input_data["service_unit"])

        return qs

    def get_response(self, request: Request) -> Response:
        input_data = self.get_input_data(request.query_params)
        report_data = self.get_data(input_data)
        serialized_report_data = self.serialize_data(report_data)

        if request.accepted_renderer.format != "xlsx":
            return Response(serialized_report_data)

        # Add totals row to xlsx output
        count = len(serialized_report_data)

        totals_row = ExcelRow()
        totals_row.cells.append(ExcelCell(column=0, value=str(_("Total"))))
        totals_row.cells.append(SumCell(column=3, target_ranges=[(0, 3, count - 1, 3)]))
        serialized_report_data.append(totals_row)

        return Response(serialized_report_data)
