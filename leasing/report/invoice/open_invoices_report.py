from itertools import groupby
from operator import itemgetter

from django import forms
from django.utils.translation import gettext_lazy as _
from rest_framework.request import Request
from rest_framework.response import Response

from leasing.enums import InvoiceState
from leasing.models import Invoice, Lease, ServiceUnit
from leasing.report.excel import (
    ExcelCell,
    ExcelRow,
    FormatType,
    PreviousRowsSumCell,
    SumCell,
)
from leasing.report.lease.common_getters import get_lease_link_data_from_related_object
from leasing.report.report_base import ReportBase


def get_lease_type(invoice: Invoice) -> str:
    return invoice.lease.identifier.type.identifier


def get_recipient_name(invoice: Invoice) -> str:
    return invoice.recipient.get_name()


def get_recipient_address(invoice: Invoice) -> str:
    return ", ".join(
        filter(
            None,
            [
                invoice.recipient.address,
                invoice.recipient.postal_code,
                invoice.recipient.city,
            ],
        )
    )


def get_due_dates_per_year(invoice: Invoice) -> int:
    first_day_of_year = invoice.due_date.replace(month=1, day=1)
    last_day_of_year = invoice.due_date.replace(month=12, day=31)
    lease: Lease = invoice.lease
    due_dates_this_year = lease.get_due_dates_for_period(
        first_day_of_year, last_day_of_year
    )
    return len(due_dates_this_year)


def get_lease_id(invoice: Invoice) -> int:
    return invoice.lease.id


def get_collection_stage(invoice: Invoice) -> str | None:
    latest_note = (
        invoice.lease.collection_notes.filter(collection_stage__isnull=False)
        .order_by("-created_at")
        .first()
    )

    if latest_note:
        return str(latest_note.collection_stage.label)


class OpenInvoicesReport(ReportBase):
    name = _("Open invoices")
    description = _('Show all the invoices that have their state as "open"')
    slug = "open_invoices"
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
        "number": {"label": _("Number")},
        "lease_type": {"source": get_lease_type, "label": _("Lease type")},
        "lease_identifier": {
            "source": get_lease_link_data_from_related_object,
            "label": _("Lease id"),
            "format": FormatType.URL.value,
        },
        "due_date": {"label": _("Due date"), "format": FormatType.DATE.value},
        "due_dates_per_year": {
            "source": get_due_dates_per_year,
            "label": _("Due dates per year"),
        },
        "total_amount": {
            "label": _("Total amount"),
            "format": FormatType.MONEY.value,
            "width": 13,
        },
        "billed_amount": {
            "label": _("Billed amount"),
            "format": FormatType.MONEY.value,
            "width": 13,
        },
        "outstanding_amount": {
            "label": _("Outstanding amount"),
            "format": FormatType.MONEY.value,
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
        "lease_database_id": {
            "source": get_lease_id,
            "label": _("Lease database id"),
        },
        "collection_stage": {
            "source": get_collection_stage,
            "label": _("Collection stage"),
            "width": 35,
        },
        "postpone_date": {
            "label": _("Postpone date"),
            "format": FormatType.DATE.value,
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

    def get_response(self, request: Request) -> Response:
        input_data = self.get_input_data(request.query_params)
        report_data = self.get_data(input_data)
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
                (totals_row_num, 5, totals_row_num, 5)
            )

        totals_row.cells.append(total_amount_sum_cell)
        totals_row.cells.append(billed_amount_sum_cell)
        totals_row.cells.append(outstanding_amount_sum_cell)
        result.append(totals_row)

        return Response(result)
