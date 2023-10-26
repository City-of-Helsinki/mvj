from itertools import groupby
from operator import itemgetter

from django import forms
from django.utils.translation import gettext_lazy as _
from rest_framework.response import Response

from leasing.enums import InvoiceState
from leasing.models import Invoice, ServiceUnit
from leasing.report.excel import ExcelCell, ExcelRow, PreviousRowsSumCell, SumCell
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


class OpenInvoicesReport(ReportBase):
    name = _("Open invoices")
    description = _('Show all the invoices that have their state as "open"')
    slug = "open_invoices"
    input_fields = {
        "service_unit": forms.ModelMultipleChoiceField(
            label=_("Service unit"), queryset=ServiceUnit.objects.all(), required=False,
        ),
        "start_date": forms.DateField(label=_("Start date"), required=True),
        "end_date": forms.DateField(label=_("End date"), required=True),
    }
    output_fields = {
        "number": {"label": _("Number")},
        "lease_type": {"source": get_lease_type, "label": _("Lease type")},
        "lease_id": {"source": get_lease_id, "label": _("Lease id")},
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
                state=InvoiceState.OPEN,
            )
            .select_related(
                "lease",
                "lease__identifier",
                "lease__identifier__type",
                "lease__identifier__district",
                "lease__identifier__municipality",
                "recipient",
            )
            .order_by("lease__identifier__type__identifier", "due_date")
        )

        if input_data["service_unit"]:
            qs = qs.filter(service_unit__in=input_data["service_unit"])

        return qs

    def get_response(self, request):
        report_data = self.get_data(self.get_input_data(request))
        serialized_report_data = self.serialize_data(report_data)

        if request.accepted_renderer.format != "xlsx":
            return Response(serialized_report_data)

        # Custom processing for xlsx output
        grouped_data = groupby(serialized_report_data, itemgetter("lease_type"))

        result = []
        totals_row_nums = []
        data_row_num = 0
        for lease_type, invoices in grouped_data:
            invoice_count = 0
            for invoice in invoices:
                result.append(invoice)
                invoice_count += 1
                data_row_num += 1

            totals_row = ExcelRow()
            totals_row.cells.append(
                ExcelCell(column=0, value="{} {}".format(lease_type, _("Total")))
            )
            totals_row.cells.append(PreviousRowsSumCell(column=4, count=invoice_count))
            totals_row.cells.append(PreviousRowsSumCell(column=5, count=invoice_count))
            totals_row.cells.append(PreviousRowsSumCell(column=6, count=invoice_count))
            result.append(totals_row)
            totals_row_nums.append(data_row_num)

            data_row_num += 1

        totals_row = ExcelRow()
        totals_row.cells.append(ExcelCell(column=0, value=str(_("Grand total"))))

        total_amount_sum_cell = SumCell(column=4)
        billed_amount_sum_cell = SumCell(column=5)
        outstanding_amount_sum_cell = SumCell(column=6)
        for totals_row_num in totals_row_nums:
            total_amount_sum_cell.add_target_range(
                (totals_row_num, 4, totals_row_num, 4)
            )
            billed_amount_sum_cell.add_target_range(
                (totals_row_num, 5, totals_row_num, 5)
            )
            outstanding_amount_sum_cell.add_target_range(
                (totals_row_num, 6, totals_row_num, 6)
            )

        totals_row.cells.append(total_amount_sum_cell)
        totals_row.cells.append(billed_amount_sum_cell)
        totals_row.cells.append(outstanding_amount_sum_cell)
        result.append(totals_row)

        return Response(result)
