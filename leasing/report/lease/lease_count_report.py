from django import forms
from django.db.models import Q
from django.db.models.aggregates import Count
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework.response import Response

from leasing.models import Lease, ServiceUnit
from leasing.report.excel import ExcelCell, ExcelRow, SumCell
from leasing.report.report_base import ReportBase


class LeaseCountReport(ReportBase):
    name = _("Lease count")
    description = _("Show the count of leases by type")
    slug = "lease_count"
    input_fields = {
        "service_unit": forms.ModelMultipleChoiceField(
            label=_("Service unit"),
            queryset=ServiceUnit.objects.all(),
            required=False,
        ),
    }
    output_fields = {
        "lease_type": {
            "source": "identifier__type__identifier",
            "label": _("Lease type"),
        },
        "description": {"label": _("Description"), "source": "identifier__type__name"},
        "count": {"label": _("Count"), "is_numeric": True},
    }

    def get_data(self, input_data):
        today = timezone.now().date()

        qs = (
            Lease.objects.filter(Q(end_date__isnull=True) | Q(end_date__gte=today))
            .values("identifier__type__identifier", "identifier__type__name")
            .annotate(count=Count("identifier__type__identifier"))
            .order_by("identifier__type__identifier")
        )

        if input_data["service_unit"]:
            qs = qs.filter(service_unit__in=input_data["service_unit"])

        return qs

    def get_response(self, request):
        report_data = self.get_data(self.get_input_data(request))
        serialized_report_data = self.serialize_data(report_data)

        if request.accepted_renderer.format != "xlsx":
            return Response(serialized_report_data)

        # Add totals row to xlsx output
        totals_row = ExcelRow()
        totals_row.cells.append(ExcelCell(column=0, value=str(_("Total"))))
        totals_row.cells.append(
            SumCell(
                column=1, target_ranges=[(0, 1, len(serialized_report_data) - 1, 1)]
            )
        )
        serialized_report_data.append(totals_row)

        return Response(serialized_report_data)
