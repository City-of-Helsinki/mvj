from django import forms
from django.db import DataError, connection
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from leasing.models import ServiceUnit
from leasing.report.lease.common_getters import LeaseLinkData
from leasing.report.report_base import ReportBase
from leasing.report.utils import InvoicingDisabledReportRow, dictfetchall


def get_lease_link_data_from_invoicing_disabled_report_row(
    disabled_report_row: InvoicingDisabledReportRow,
) -> LeaseLinkData:
    try:
        return {
            "id": disabled_report_row["lease_id"],
            "identifier": disabled_report_row["lease_identifier"],
        }
    except KeyError:
        return {
            "id": None,
            "identifier": None,
        }


INVOICING_DISABLED_REPORT_SQL = """
    SELECT NULL AS "section",
        li.identifier AS "lease_identifier",
        l.id AS "lease_id",
        l.start_date,
        l.end_date
    FROM leasing_lease l
    INNER JOIN leasing_leaseidentifier li
        ON l.identifier_id = li.id
    LEFT JOIN leasing_leasetype lt
            ON lt.id = l.type_id
    INNER JOIN leasing_rent r
        ON l.id = r.lease_id
            AND r.deleted IS NULL
            AND (r.start_date IS NULL OR r.start_date <= %(today)s)
            AND (r.end_date IS NULL OR r.end_date >= %(today)s)
            AND r.type != 'free'
    WHERE (l.end_date IS NULL OR l.end_date >= %(today)s)
        AND l.start_date IS NOT NULL
        AND l.state IN ('lease', 'short_term_lease', 'long_term_lease')
        AND l.service_unit_id = ANY(%(service_units)s)
        AND l.deleted IS NULL
        AND l.invoicing_enabled_at IS NULL
        AND lt.identifier NOT IN ('MA', 'TY')
    ORDER BY li.identifier;
"""


class LeaseInvoicingDisabledReport(ReportBase):
    name = _("Leases where invoicing is disabled")
    description = _("Shows active leases where invoicing is not enabled")
    slug = "lease_invoicing_disabled"
    input_fields = {
        "service_unit": forms.ModelMultipleChoiceField(
            label=_("Service unit"),
            queryset=ServiceUnit.objects.all(),
            required=False,
        ),
    }
    output_fields = {
        "lease_identifier": {
            "source": get_lease_link_data_from_invoicing_disabled_report_row,
            "label": _("Lease id"),
        },
        "start_date": {"label": _("Start date"), "format": "date"},
        "end_date": {"label": _("End date"), "format": "date"},
    }

    def get_data(self, input_data):
        today = timezone.now().date()

        if input_data["service_unit"]:
            service_unit_ids = [su.id for su in input_data["service_unit"]]
        else:
            service_unit_ids = [su.id for su in ServiceUnit.objects.all()]

        rows = []
        with connection.cursor() as cursor:
            try:
                cursor.execute(
                    INVOICING_DISABLED_REPORT_SQL,
                    {"service_units": service_unit_ids, "today": today},
                )
                rows = dictfetchall(cursor)
            except DataError:
                pass

        return rows
