import datetime
from collections import defaultdict
from fractions import Fraction
from io import BytesIO
from operator import itemgetter

import xlsxwriter
from django import forms
from django.db import DataError, connection
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy
from enumfields import Enum
from enumfields.drf import EnumField
from rest_framework.response import Response

from leasing.models import ReceivableType, ServiceUnit
from leasing.report.excel import FormatType
from leasing.report.lease.invoicing_disabled_report import INVOICING_DISABLED_REPORT_SQL
from leasing.report.report_base import ReportBase
from leasing.report.utils import (
    calculate_invoice_billing_period_days,
    dictfetchall,
    get_lease_period,
)

# Ids of receivable types that are not included in the gaps in the billing periods report
# These lack the start and end dates of the billing periods by default,
# or have a billing date range of only one day,
# which make them exceptions to the billing periods.
EXCLUDED_RECEIVABLE_TYPE_NAMES = [
    "Korko",
    "Yhteismarkkinointi (sis. ALV)",
    "Kiinteistötoimitukset (tonttijaot, lohkomiset, rekisteröimiskustannukset, rasitteet)",
    "Rahavakuus",
]


class InvoicingReviewSection(Enum):
    INVOICING_NOT_ENABLED = "invoicing_not_enabled"
    RENT_INFO_NOT_COMPLETE = "rent_info_not_complete"
    NO_RENTS = "no_rents"
    NO_DUE_DATE = "no_due_date"
    ONE_TIME_RENTS_WITH_NO_INVOICE = "one_time_rents_with_no_invoice"
    INCORRECT_MANAGEMENT_SHARES = "incorrect_management_shares"
    INCORRECT_RENT_SHARES = "incorrect_rent_shares"
    NO_TENANT_CONTACT = "no_tenant_contact"
    NO_LEASE_AREA = "no_lease_area"
    INDEX_TYPE_MISSING = "index_type_missing"
    ONGOING_RENT_WITHOUT_RENT_SHARES = "ongoing_rent_without_rent_shares"
    GAPS_IN_BILLING_PERIODS = "gaps_in_billing_periods"

    class Labels:
        INVOICING_NOT_ENABLED = pgettext_lazy(
            "Invoicing review", "Invoicing not enabled"
        )
        RENT_INFO_NOT_COMPLETE = pgettext_lazy(
            "Invoicing review", "Rent info not complete"
        )
        NO_RENTS = pgettext_lazy("Invoicing review", "No rents")
        NO_DUE_DATE = pgettext_lazy("Invoicing review", "No due date")
        ONE_TIME_RENTS_WITH_NO_INVOICE = pgettext_lazy(
            "Invoicing review", "One time rents with no invoice"
        )
        INCORRECT_MANAGEMENT_SHARES = pgettext_lazy(
            "Invoicing review", "Incorrect management shares"
        )
        INCORRECT_RENT_SHARES = pgettext_lazy(
            "Invoicing review", "Incorrect rent shares"
        )
        NO_TENANT_CONTACT = pgettext_lazy("Invoicing review", "No tenant contact")
        NO_LEASE_AREA = pgettext_lazy("Invoicing review", "No lease area")
        INDEX_TYPE_MISSING = pgettext_lazy("Invoicing review", "Index type missing")
        ONGOING_RENT_WITHOUT_RENT_SHARES = pgettext_lazy(
            "Invoicing review", "Ongoing rent without rent shares"
        )
        GAPS_IN_BILLING_PERIODS = pgettext_lazy(
            "Invoicing review", "Gaps in billing periods"
        )


INVOICING_REVIEW_QUERIES = {
    "invoicing_not_enabled": INVOICING_DISABLED_REPORT_SQL,
    "rent_info_not_complete": """
        SELECT NULL AS "section",
            li.identifier AS "lease_identifier",
            l.start_date,
            l.end_date
        FROM leasing_lease l
        INNER JOIN leasing_leaseidentifier li
            ON l.identifier_id = li.id
        WHERE (l.end_date IS NULL OR l.end_date >= %(today)s)
            AND l.start_date IS NOT NULL
            AND l.service_unit_id = ANY(%(service_units)s)
            AND l.deleted IS NULL
            AND l.state IN ('lease', 'short_term_lease', 'long_term_lease')
            AND l.is_rent_info_complete = FALSE
        GROUP BY l.id,
                li.id
        ORDER BY li.identifier;
    """,
    "no_rents": """
        SELECT NULL AS "section",
            li.identifier AS "lease_identifier",
            l.start_date,
            l.end_date
        FROM leasing_lease l
        LEFT OUTER JOIN leasing_rent r
            ON l.id = r.lease_id
                AND r.deleted IS NULL
                AND (r.start_date IS NULL OR r.start_date <= %(today)s)
                AND (r.end_date IS NULL OR r.end_date >= %(today)s)
        INNER JOIN leasing_leaseidentifier li
            ON (l.identifier_id = li.id)
        WHERE (l.end_date IS NULL OR l.end_date >= %(today)s)
            AND l.service_unit_id = ANY(%(service_units)s)
            AND l.deleted IS NULL
            AND l.state NOT IN ('reservation', 'power_of_attorney')
        GROUP BY l.id,
                li.id
        HAVING COUNT(r.id) = 0
    """,
    "no_due_date": """
        SELECT NULL AS "section",
            li.identifier AS "lease_identifier",
            l.start_date,
            l.end_date
        FROM leasing_lease l
        INNER JOIN leasing_leaseidentifier li
            ON l.identifier_id = li.id
        LEFT OUTER JOIN leasing_rent r
            ON l.id = r.lease_id
                AND r.due_dates_type = 'custom'
                AND r.deleted IS NULL
                AND (r.start_date IS NULL OR r.start_date <= %(today)s)
        LEFT OUTER JOIN leasing_rentduedate rdd
            ON r.id = rdd.rent_id
                AND rdd.deleted IS NULL
        LEFT OUTER JOIN leasing_rent r2
            ON l.id = r2.lease_id
                AND r2.type IN ('index', 'fixed')
                AND r2.due_dates_type = 'fixed'
                AND r2.due_dates_per_year IS NULL
                AND r2.deleted IS NULL
                AND (r2.start_date IS NULL OR r2.start_date <= %(today)s)
        WHERE (l.end_date IS NULL OR l.end_date >= %(today)s)
            AND l.service_unit_id = ANY(%(service_units)s)
            AND l.deleted IS NULL
            AND l.state NOT IN ('reservation', 'power_of_attorney')
        GROUP BY l.id,
                li.id
        HAVING (
               (COUNT(r.id) > 0 AND COUNT(rdd.id) = 0)
               OR COUNT(r2.id) > 0
            )
    """,
    "index_type_missing": """
        SELECT NULL as "section",
            li.identifier AS "lease_identifier",
            l.start_date,
            l.end_date
        FROM leasing_lease l
        INNER JOIN leasing_leaseidentifier li
            ON l.identifier_id = li.id
        INNER JOIN leasing_rent r
            ON l.id = r.lease_id
                AND r.deleted IS NULL
                AND (r.start_date IS NULL OR r.start_date <= %(today)s)
                AND (r.end_date IS NULL OR r.end_date >= %(today)s)
                AND r.type = 'index'
                AND r.index_type IS NULL
        WHERE (l.end_date IS NULL OR l.end_date >= %(today)s)
            AND l.service_unit_id = ANY(%(service_units)s)
            AND l.start_date IS NOT NULL
            AND l.deleted IS NULL
            AND l.state NOT IN ('reservation', 'power_of_attorney')
        GROUP BY l.id,
                 li.id
    """,
    "one_time_rents_with_no_invoice": """
        SELECT NULL as "section",
            li.identifier AS "lease_identifier",
            l.start_date,
            l.end_date
        FROM leasing_lease l
        INNER JOIN leasing_rent r
            ON l.id = r.lease_id
                AND r.deleted IS NULL
                AND (r.start_date IS NULL OR r.start_date <= %(today)s)
                AND r.type = 'one_time'
        INNER JOIN leasing_leaseidentifier li
            ON l.identifier_id = li.id
        LEFT OUTER JOIN leasing_invoice i
            ON l.id = i.lease_id
        WHERE (l.end_date IS NULL OR l.end_date >= %(today)s)
            AND l.service_unit_id = ANY(%(service_units)s)
            AND l.deleted IS NULL
            AND l.state NOT IN ('reservation', 'power_of_attorney')
        GROUP BY l.id,
                li.id
        HAVING COUNT(i.id) = 0
    """,
    "no_tenant_contact": """
        SELECT NULL as "section",
            li.identifier AS "lease_identifier",
            l.start_date,
            l.end_date
        FROM leasing_lease l
        INNER JOIN leasing_leaseidentifier li
            ON l.identifier_id = li.id
        LEFT OUTER JOIN
            (SELECT t.id, t.lease_id
                FROM leasing_tenant t
                    INNER JOIN leasing_tenantcontact tc
                    ON t.id = tc.tenant_id
                        AND tc.type = 'tenant'
                        AND (tc.end_date IS NULL OR tc.end_date > %(today)s)
                        AND tc.deleted IS NULL
                WHERE t.deleted IS NULL
                GROUP BY t.id
            ) tt ON tt.lease_id = l.id
        WHERE (l.end_date IS NULL OR l.end_date >= %(today)s)
            AND l.service_unit_id = ANY(%(service_units)s)
            AND l.deleted IS NULL
            AND l.state NOT IN ('reservation', 'power_of_attorney')
        GROUP BY l.id,
                li.id
        HAVING COUNT(tt.id) = 0
    """,
    "no_lease_area": """
        SELECT NULL AS "section",
            li.identifier AS "lease_identifier",
            l.start_date,
            l.end_date
        FROM leasing_lease l
        LEFT OUTER JOIN leasing_leasearea la
            ON l.id = la.lease_id
        INNER JOIN leasing_leaseidentifier li
            ON l.identifier_id = li.id
        WHERE (l.end_date IS NULL OR l.end_date >= %(today)s)
            AND l.service_unit_id = ANY(%(service_units)s)
            AND l.deleted IS NULL
            AND l.state NOT IN ('reservation', 'power_of_attorney')
        GROUP BY l.id,
                li.id
        HAVING COUNT(la.id) = 0
    """,
}


class InvoicingReviewReport(ReportBase):
    name = _("Invoicing review")
    description = _("Show leases that might have errors in their invoicing")
    slug = "invoicing_review"
    input_fields = {
        "service_unit": forms.ModelMultipleChoiceField(
            label=_("Service unit"),
            queryset=ServiceUnit.objects.all(),
            required=False,
        ),
    }
    output_fields = {
        "section": {
            "label": pgettext_lazy("Invoicing review", "Section"),
            "serializer_field": EnumField(enum=InvoicingReviewSection),
        },
        "lease_identifier": {"label": _("Lease id")},
        "start_date": {"label": _("Start date"), "format": "date"},
        "end_date": {"label": _("End date"), "format": "date"},
        "note": {"label": _("Note")},
    }
    automatic_excel_column_labels = False
    is_already_sorted = True

    def get_incorrect_rent_shares_data(self, service_unit_ids, cursor):
        today = datetime.date.today()

        query = """
            SELECT li.identifier as lease_identifier,
                   l.start_date,
                   l.end_date,
                   array_agg(share) AS shares
              FROM leasing_lease l
                   INNER JOIN leasing_leaseidentifier li
                   ON l.identifier_id = li.id
                   INNER JOIN
                   (SELECT t.id,
                           t.lease_id,
                           array [trs.intended_use_id, trs.share_numerator, trs.share_denominator] AS share
                      FROM leasing_tenant t
                           INNER JOIN leasing_tenantcontact tc
                           ON t.id = tc.tenant_id
                              AND tc.type = 'tenant'
                              AND tc.start_date <= %(today)s
                              AND (tc.end_date IS NULL OR tc.end_date >= %(today)s)
                              AND tc.deleted IS NULL
                           INNER JOIN leasing_tenantrentshare trs
                           ON t.id = trs.tenant_id
                              AND trs.deleted IS NULL
                     WHERE t.deleted IS NULL
                   ) tt ON tt.lease_id = l.id
            WHERE (l.end_date IS NULL OR l.end_date >= %(today)s)
              AND l.service_unit_id = ANY(%(service_units)s)
              AND l.deleted IS NULL
            GROUP BY l.id,
                     li.id;
        """

        cursor.execute(query, {"service_units": service_unit_ids, "today": today})

        data = []
        for row in dictfetchall(cursor):
            share_sums = defaultdict(Fraction)
            for intended_use_id, numerator, denominator in row["shares"]:
                share_sums[intended_use_id] += Fraction(
                    int(numerator), int(denominator)
                )

            invalid_shares = []
            for intended_use_id, share_sum in share_sums.items():
                if share_sum != Fraction(1):
                    invalid_shares.append(str(share_sum))

            if invalid_shares:
                data.append(
                    {
                        "section": None,
                        "lease_identifier": row["lease_identifier"],
                        "start_date": row["start_date"],
                        "end_date": row["end_date"],
                        "note": ", ".join(invalid_shares),
                    }
                )

        return data

    def get_ongoing_rent_without_rent_shares_data(self, service_unit_ids, cursor):
        today = datetime.date.today()

        query = """
            SELECT li.identifier as lease_identifier,
                   l.start_date,
                   l.end_date
              FROM leasing_lease l
                   INNER JOIN leasing_leaseidentifier li
                   ON l.identifier_id = li.id
                   INNER JOIN leasing_rent r
                        ON l.id = r.lease_id
                        AND r.deleted IS NULL
                        AND (r.start_date IS NULL OR r.start_date <= %(today)s)
                        AND (r.end_date IS NULL OR r.end_date >= %(today)s)
                   INNER JOIN
                   (SELECT t.id,
                           t.lease_id,
                           trs.id as trs_id
                      FROM leasing_tenant t
                           INNER JOIN leasing_tenantcontact tc
                           ON t.id = tc.tenant_id
                              AND tc.type = 'tenant'
                              AND tc.start_date <= %(today)s
                              AND (tc.end_date IS NULL OR tc.end_date >= %(today)s)
                              AND tc.deleted IS NULL
                           LEFT JOIN leasing_tenantrentshare trs
                           ON t.id = trs.tenant_id
                              AND trs.deleted IS NULL
                     WHERE t.deleted IS NULL
                   ) tt ON tt.lease_id = l.id
            WHERE (l.end_date IS NULL OR l.end_date >= %(today)s)
              AND l.service_unit_id = ANY(%(service_units)s)
              AND l.deleted IS NULL
              AND tt.trs_id IS NULL
            GROUP BY l.id,
                     li.id;
        """

        cursor.execute(query, {"service_units": service_unit_ids, "today": today})

        data = []
        for row in dictfetchall(cursor):
            data.append(
                {
                    "section": None,
                    "lease_identifier": row["lease_identifier"],
                    "start_date": row["start_date"],
                    "end_date": row["end_date"],
                    "note": "",
                }
            )

        return data

    def get_incorrect_management_shares_data(self, service_unit_ids, cursor):
        today = datetime.date.today()

        query = """
            SELECT li.identifier as "lease_identifier",
                   l."start_date",
                   l."end_date",
                   array_agg(tt.share) AS "shares"
              FROM "leasing_lease" l
                   INNER JOIN "leasing_leaseidentifier" li
                   ON l."identifier_id" = li."id"
                   INNER JOIN
                   (SELECT t.id,
                           t.lease_id,
                           CONCAT(t.share_numerator, '/', t.share_denominator) AS share
                      FROM "leasing_tenant" t
                           INNER JOIN leasing_tenantcontact tc
                           ON t.id = tc.tenant_id
                           AND tc.type = 'tenant'
                           AND tc.start_date <= %(today)s
                           AND (tc.end_date IS NULL OR tc.end_date >= %(today)s)
                           AND tc.deleted IS NULL
                     WHERE t.deleted IS NULL
                     GROUP BY t.id
                   ) tt ON tt.lease_id = l.id
            WHERE (l."end_date" IS NULL OR l."end_date" >= %(today)s)
              AND l.service_unit_id = ANY(%(service_units)s)
              AND l."deleted" IS NULL
            GROUP BY l."id",
                     li."id"
        """

        cursor.execute(query, {"service_units": service_unit_ids, "today": today})

        data = []
        for row in dictfetchall(cursor):
            shares_total = Fraction()
            for share in row["shares"]:
                (numerator, denominator) = share.split("/")
                shares_total += Fraction(int(numerator), int(denominator))

            if shares_total != Fraction(1):
                data.append(
                    {
                        "section": None,
                        "lease_identifier": row["lease_identifier"],
                        "start_date": row["start_date"],
                        "end_date": row["end_date"],
                        "note": str(shares_total),
                    }
                )

        return data

    def get_gaps_in_billing_periods_data(self, service_unit_ids, cursor):

        query = """
            SELECT li.identifier AS "lease_identifier",
                l.id AS "lease_id",
                l.start_date,
                l.end_date,
                r.id AS "rent_id",
                r.start_date AS "rent_start_date",
                r.end_date AS "rent_end_date",
                i.id AS "invoice_id",
                i.billing_period_start_date,
                i.billing_period_end_date
            FROM leasing_lease l
            INNER JOIN leasing_leaseidentifier li
                ON l.identifier_id = li.id
            INNER JOIN leasing_rent r
                ON l.id = r.lease_id
            LEFT JOIN leasing_invoice i
                ON l.id = i.lease_id
            INNER JOIN leasing_invoicerow ir
                ON i.id = ir.invoice_id
            WHERE (l.end_date IS NULL OR l.end_date >= %(today)s)
                AND (l.start_date IS NOT NULL AND l.start_date <= %(today)s)
                AND l.service_unit_id = ANY(%(service_units)s)
                AND l.deleted IS NULL
                AND l.state NOT IN ('reservation', 'power_of_attorney')
                AND r.deleted IS NULL
                AND r."type" != 'free'
                AND (r.start_date IS NULL OR r.start_date <= %(today)s)
                AND (r.end_date IS NULL OR r.end_date >= %(today)s)
                AND i.deleted IS NULL
                AND i.deleted_by_cascade IS false
                AND ir.deleted IS NULL
                AND ir.receivable_type_id != ANY(%(excluded_receivable_type_ids)s)
            ORDER BY li.identifier ASC;
        """

        today = datetime.date.today()

        excluded_receivable_type_ids = [
            id
            for id in ReceivableType.objects.filter(
                name__in=EXCLUDED_RECEIVABLE_TYPE_NAMES
            ).values_list("id", flat=True)
        ]

        cursor.execute(
            query,
            {
                "service_units": service_unit_ids,
                "today": today,
                "excluded_receivable_type_ids": excluded_receivable_type_ids,
            },
        )

        billing_periods_data = dictfetchall(cursor)

        data = []

        for i, billing_period_data_row in enumerate(billing_periods_data):
            # Initialize variables
            if i == 0:
                # Active rent period means the date range defined by
                # primarily the rent's start and end dates,
                # and secondarily by the lease's start and end dates.
                lease_period_start = None
                lease_period_end = None
                lease_period_days = 0

                # Invoiced period means the date range accumulated
                # by the billing periods of lease's invoices.
                # Their total number of days should match the active rent period days.
                # If it doesn't, it has gaps and therefore is added to the report.
                invoiced_period_days = 0
                lease_has_gaps = False

                current_lease_id = None
                next_lease_id = None

            current_lease_id = billing_period_data_row["lease_id"]
            next_lease_id = (
                billing_periods_data[i + 1]["lease_id"]
                if i + 1 < len(billing_periods_data)
                else None
            )

            if lease_has_gaps and current_lease_id == next_lease_id:
                continue

            billing_period_increment = calculate_invoice_billing_period_days(
                billing_period_data_row["billing_period_start_date"],
                billing_period_data_row["billing_period_end_date"],
                today,
            )

            if billing_period_increment is None:
                lease_has_gaps = True
                continue

            invoiced_period_days += billing_period_increment

            if current_lease_id != next_lease_id:
                lease_period_start, lease_period_end = get_lease_period(
                    billing_period_data_row,
                    today,
                )
                lease_period_days = (lease_period_end - lease_period_start).days + 1

                if lease_period_days != invoiced_period_days:
                    lease_has_gaps = True

                if lease_has_gaps:
                    data.append(
                        {
                            "section": None,
                            "lease_identifier": billing_period_data_row[
                                "lease_identifier"
                            ],
                        }
                    )
                lease_period_start = None
                lease_period_end = None
                lease_period_days = 0
                invoiced_period_days = 0
                lease_has_gaps = False

        return data

    def get_data(self, input_data):
        today = datetime.date.today()

        if input_data["service_unit"]:
            service_unit_ids = [su.id for su in input_data["service_unit"]]
        else:
            service_unit_ids = [su.id for su in ServiceUnit.objects.all()]

        result = []
        with connection.cursor() as cursor:
            for lease_list_type in InvoicingReviewSection:
                result.append(
                    {
                        "section": lease_list_type.value,
                        "lease_identifier": None,
                        "start_date": None,
                        "end_date": None,
                    }
                )

                rows = []
                try:
                    if lease_list_type.value in INVOICING_REVIEW_QUERIES:
                        cursor.execute(
                            INVOICING_REVIEW_QUERIES[lease_list_type.value],
                            {"service_units": service_unit_ids, "today": today},
                        )
                        rows = dictfetchall(cursor)

                    if hasattr(self, f"get_{lease_list_type.value}_data"):
                        rows = getattr(self, f"get_{lease_list_type.value}_data")(
                            service_unit_ids, cursor
                        )
                except DataError as e:
                    rows = [
                        {
                            "section": None,
                            "lease_identifier": None,
                            "start_date": None,
                            "end_date": None,
                            "note": f"Query error when generating report: {e}",
                        }
                    ]

                rows.sort(key=itemgetter("lease_identifier"))
                result.extend(rows)

        return result

    def get_response(self, request):
        report_data = self.get_data(self.get_input_data(request))
        serialized_report_data = self.serialize_data(report_data)

        if request.accepted_renderer.format != "xlsx":
            return Response(serialized_report_data)

        final_report_data = {}
        section = ""
        for datum in serialized_report_data:
            if datum["section"]:
                section = str(InvoicingReviewSection(datum["section"]).label)
                final_report_data[section] = []
            else:
                final_report_data[section].append(datum)

        return Response(final_report_data)

    def data_as_excel(self, data_sections):
        """
        Overrides report base function so that data sections can be put on separate sheets.
        """
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        formats = {
            FormatType.BOLD: workbook.add_format({"bold": True}),
            FormatType.DATE: workbook.add_format({"num_format": "dd.mm.yyyy"}),
            FormatType.MONEY: workbook.add_format({"num_format": "#,##0.00 €"}),
            FormatType.BOLD_MONEY: workbook.add_format(
                {"bold": True, "num_format": "#,##0.00 €"}
            ),
            FormatType.PERCENTAGE: workbook.add_format({"num_format": "0.0 %"}),
            FormatType.AREA: workbook.add_format({"num_format": r"#,##0.00 \m\²"}),
        }

        # worksheet max length name is 31 so need to truncate and make sure there are no duplicates
        worksheet_names_dict = self.get_worksheet_names_dict(data_sections)

        for key, rows in data_sections.items():
            worksheet_name = worksheet_names_dict[key]
            worksheet = workbook.add_worksheet(worksheet_name)
            row_num = self.write_worksheet_heading(worksheet, formats, key)
            for row in rows:
                self.write_dict_row_to_worksheet(worksheet, formats, row_num, row)
                row_num += 1

        workbook.close()
        return output.getvalue()

    def get_worksheet_names_dict(self, data_sections):
        """
        Returns a dict with key as original section name and value the truncated and numbered worksheet name
        """

        # worksheet max length name is 31 so need to truncate
        worksheet_names_dict = dict(
            map(
                lambda key: (key, (key[:29] + "..") if len(key) > 31 else key),
                data_sections.keys(),
            )
        )

        # need to make sure there are no duplicated worksheet names so add numbering to end if duplicates
        duplicate_name_count_dict = {}
        for worksheet_name, truncated_worksheet_name in worksheet_names_dict.items():
            if truncated_worksheet_name in duplicate_name_count_dict:
                duplicate_name_count_dict[truncated_worksheet_name] += 1
                str_num_to_append = str(
                    duplicate_name_count_dict[truncated_worksheet_name]
                )
                worksheet_names_dict[worksheet_name] = (
                    truncated_worksheet_name[: -(1 + len(str_num_to_append))]
                    + "_"
                    + str(duplicate_name_count_dict[truncated_worksheet_name])
                )
            else:
                duplicate_name_count_dict[truncated_worksheet_name] = 1

        return worksheet_names_dict

    def write_worksheet_heading(self, worksheet, formats, section):
        """
        Sets column width and writes report name, description, section and column labels to worksheet.
        Returns row number after column labels:
        """

        # set column widths
        worksheet.set_column(0, 0, 10)
        worksheet.set_column(0, 1, 10)
        worksheet.set_column(0, 2, 10)
        worksheet.set_column(0, 3, 10)
        worksheet.set_column(0, 4, 10)

        # On the first row print the report name
        worksheet.write(0, 0, str(self.name), formats[FormatType.BOLD])

        # On the second row print the report description
        worksheet.write(1, 0, str(self.description))

        # Write metadata and column labels on excel
        row_num = self.write_input_field_value_rows(worksheet, self.form, 3, formats)
        row_num += 1
        worksheet.write(row_num, 0, section, formats[FormatType.BOLD])
        row_num += 2
        self.write_worksheet_labels(row_num, worksheet, formats[FormatType.BOLD])
        row_num += 1

        return row_num

    def write_worksheet_labels(self, row_num, worksheet, format):
        worksheet.write(row_num, 1, "Lease id", format)
        worksheet.write(row_num, 2, "Start date", format)
        worksheet.write(row_num, 3, "End date", format)
        worksheet.write(row_num, 4, "Note", format)
