from django import forms
from django.utils.translation import gettext_lazy as _
from enumfields.drf import EnumField
from rest_framework.response import Response

from leasing.enums import InvoiceState
from leasing.models import Invoice, LeaseType
from leasing.report.excel import ExcelCell, ExcelRow, SumCell
from leasing.report.report_base import ReportBase


def get_lease_type(obj):
    return obj.lease.identifier.type.identifier


def get_lease_id(obj):
    return obj.lease.get_identifier_string()


def get_recipient_name(obj):
    return obj.recipient.get_name()


def get_recipient_address(obj):
    return ", ".join(
        filter(
            None, [obj.recipient.address, obj.recipient.postal_code, obj.recipient.city]
        )
    )


def get_receivable_types(obj):
    receivable_types = {str(row.receivable_type) for row in obj.rows.all()}
    return ", ".join(receivable_types)


class InvoicesInPeriodReport(ReportBase):
    name = _("Invoces in period")
    description = _(
        "Show all the invoices that have due date between start and end date"
    )
    slug = "invoices_in_period"
    input_fields = {
        "start_date": forms.DateField(label=_("Start date"), required=True),
        "end_date": forms.DateField(label=_("End date"), required=True),
        "lease_type": forms.ModelChoiceField(
            label=_("Laskutuslaji"),
            queryset=LeaseType.objects.all(),
            empty_label=None,
            required=False,
        ),
        "invoice_state": forms.ChoiceField(
            label=_("Invoice state"), required=False, choices=InvoiceState.choices()
        ),
    }
    output_fields = {
        "number": {"label": _("Number"), "is_numeric": True},
        "receivable_type": {
            "source": get_receivable_types,
            "label": _("Receivable type"),
        },
        "lease_type": {"source": get_lease_type, "label": _("Lease type")},
        "lease_id": {"source": get_lease_id, "label": _("Lease id")},
        "state": {
            "label": _("State"),
            "serializer_field": EnumField(enum=InvoiceState),
        },
        "due_date": {"label": _("Due date"), "format": "date"},
        "total_amount": {"label": _("Total amount"), "format": "money", "width": 13},
        "billed_amount": {"label": _("Billed amount"), "format": "money", "width": 13},
        "outstanding_amount": {
            "label": _("Outstanding amount"),
            "format": "money",
            "width": 13,
        },
        "recipient_name": {
            "source": get_recipient_name,
            "label": _("Recipient name"),
            "width": 50,
        },
        "recipient_address": {
            "source": get_recipient_address,
            "label": _("Recipient address"),
            "width": 50,
        },
    }

    def get_data(self, input_data):
        qs = (
            Invoice.objects.filter(
                due_date__gte=input_data["start_date"],
                due_date__lte=input_data["end_date"],
            )
            .select_related(
                "lease",
                "lease__identifier",
                "lease__identifier__type",
                "lease__identifier__district",
                "lease__identifier__municipality",
                "recipient",
            )
            .prefetch_related("rows", "rows__receivable_type")
            .order_by("lease__identifier__type__identifier", "due_date")
        )

        if input_data["invoice_state"]:
            qs = qs.filter(state=input_data["invoice_state"])

        if input_data["lease_type"]:
            qs = qs.filter(lease__identifier__type=input_data["lease_type"])

        return qs

    def get_response(self, request):
        report_data = self.get_data(self.get_input_data(request))
        serialized_report_data = self.serialize_data(report_data)

        if request.accepted_renderer.format != "xlsx":
            return Response(serialized_report_data)

        # Add totals row to xlsx output
        invoice_count = len(serialized_report_data)

        totals_row = ExcelRow()
        totals_row.cells.append(ExcelCell(column=0, value=str(_("Total"))))
        totals_row.cells.append(
            SumCell(column=5, target_ranges=[(0, 5, invoice_count - 1, 5)])
        )
        totals_row.cells.append(
            SumCell(column=6, target_ranges=[(0, 6, invoice_count - 1, 6)])
        )
        totals_row.cells.append(
            SumCell(column=7, target_ranges=[(0, 7, invoice_count - 1, 7)])
        )
        serialized_report_data.append(totals_row)

        return Response(serialized_report_data)
