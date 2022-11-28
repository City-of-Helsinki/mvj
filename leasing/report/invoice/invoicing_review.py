import datetime
from collections import defaultdict
from fractions import Fraction
from operator import itemgetter

from django.db import connection
from django.utils.translation import pgettext_lazy
from django.utils.translation import ugettext_lazy as _
from enumfields import Enum
from enumfields.drf import EnumField
from rest_framework.response import Response

from leasing.report.excel import ExcelCell, ExcelRow, FormatType
from leasing.report.report_base import ReportBase


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


INVOICING_REVIEW_QUERIES = {
    "invoicing_not_enabled": """
        SELECT NULL AS "section",
               li.identifier AS "lease_id",
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
                  AND r.type != 'free'
         WHERE (l.end_date IS NULL OR l.end_date >= %(today)s)
           AND l.start_date IS NOT NULL
           AND l.state IN ('lease', 'short_term_lease', 'long_term_lease')
           AND l.deleted IS NULL
           AND l.is_invoicing_enabled = FALSE
         GROUP BY l.id,
                  li.identifier
         ORDER BY li.identifier;
    """,
    "rent_info_not_complete": """
        SELECT NULL AS "section",
               li.identifier AS "lease_id",
               l.start_date,
               l.end_date
          FROM leasing_lease l
               INNER JOIN leasing_leaseidentifier li
               ON l.identifier_id = li.id
         WHERE (l.end_date IS NULL OR l.end_date >= %(today)s)
           AND l.start_date IS NOT NULL
           AND l.deleted IS NULL
           AND l.state IN ('lease', 'short_term_lease', 'long_term_lease')
           AND l.is_rent_info_complete = FALSE
         GROUP BY l.id,
                 li.id
         ORDER BY li.identifier;
    """,
    "no_rents": """
        SELECT NULL AS "section",
               li.identifier AS "lease_id",
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
          AND l.deleted IS NULL
        GROUP BY l.id,
                 li.id
        HAVING COUNT(r.id) = 0
    """,
    "no_due_date": """
        SELECT NULL AS "section",
               li.identifier AS "lease_id",
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
          AND l.deleted IS NULL
        GROUP BY l.id,
                 li.id
        HAVING (
               (COUNT(r.id) > 0 AND COUNT(rdd.id) = 0)
               OR COUNT(r2.id) > 0
               )
    """,
    "index_type_missing": """
        SELECT NULL as "section",
               li.identifier AS "lease_id",
               l.start_date,
               l.end_date
         FROM leasing_lease l
              INNER JOIN leasing_leaseidentifier li ON l.identifier_id = li.id
              INNER JOIN leasing_rent r
              ON l.id = r.lease_id
                 AND r.deleted IS NULL
                 AND (r.start_date IS NULL OR r.start_date <= %(today)s)
                 AND (r.end_date IS NULL OR r.end_date >= %(today)s)
                 AND r.type = 'index'
                 AND r.index_type IS NULL
        WHERE (l.end_date IS NULL OR l.end_date >= %(today)s)
          AND l.start_date IS NOT NULL
          AND l.deleted IS NULL
        GROUP BY l.id,
                 li.id
    """,
    "one_time_rents_with_no_invoice": """
        SELECT NULL as "section",
               li.identifier AS "lease_id",
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
           AND l.deleted IS NULL
         GROUP BY l.id,
                  li.id
        HAVING COUNT(i.id) = 0
    """,
    "no_tenant_contact": """
        SELECT NULL as "section",
               li.identifier AS "lease_id",
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
           AND l.deleted IS NULL
         GROUP BY l.id,
                  li.id
        HAVING COUNT(tt.id) = 0
    """,
    "no_lease_area": """
        SELECT NULL AS "section",
               li.identifier AS "lease_id",
               l.start_date,
               l.end_date
          FROM leasing_lease l
               LEFT OUTER JOIN leasing_leasearea la
               ON l.id = la.lease_id
               INNER JOIN leasing_leaseidentifier li
               ON l.identifier_id = li.id
         WHERE (l.end_date IS NULL OR l.end_date >= %(today)s)
           AND l.deleted IS NULL
        GROUP BY l.id,
                 li.id
        HAVING COUNT(la.id) = 0
    """,
}


# From Django docs
def dictfetchall(cursor):
    """Return all rows from a cursor as a dict"""
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


class InvoicingReviewReport(ReportBase):
    name = _("Invoicing review")
    description = _("Show leases that might have errors in their invoicing")
    slug = "invoicing_review"
    input_fields = {}
    output_fields = {
        "section": {
            "label": pgettext_lazy("Invoicing review", "Section"),
            "serializer_field": EnumField(enum=InvoicingReviewSection),
        },
        "lease_id": {"label": _("Lease id")},
        "start_date": {"label": _("Start date"), "format": "date"},
        "end_date": {"label": _("End date"), "format": "date"},
        "note": {"label": _("Note")},
    }
    automatic_excel_column_labels = False
    is_already_sorted = True

    def get_incorrect_rent_shares_data(self, cursor):
        today = datetime.date.today()

        query = """
            SELECT li.identifier as lease_id,
                   l.start_date,
                   l.end_date,
                   array_agg(share) AS shares
              FROM leasing_lease l
                   INNER JOIN leasing_leaseidentifier li
                   ON l.identifier_id = li.id
                   INNER JOIN
                   (SELECT t.id,
                           t.lease_id,
                           array_agg(array [trs.intended_use_id, trs.share_numerator, trs.share_denominator]) AS share
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
                     GROUP BY t.id
                   ) tt ON tt.lease_id = l.id
            WHERE (l.end_date IS NULL OR l.end_date >= %(today)s)
              AND l.deleted IS NULL
            GROUP BY l.id,
                     li.id;
        """

        cursor.execute(query, {"today": today})

        data = []
        for row in dictfetchall(cursor):
            share_sums = defaultdict(Fraction)
            for share in row["shares"]:
                for (intended_use_id, numerator, denominator) in share:
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
                        "lease_id": row["lease_id"],
                        "start_date": row["start_date"],
                        "end_date": row["end_date"],
                        "note": ", ".join(invalid_shares),
                    }
                )

        return data

    def get_incorrect_management_shares_data(self, cursor):
        today = datetime.date.today()

        query = """
            SELECT li.identifier as "lease_id",
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
              AND l."deleted" IS NULL
            GROUP BY l."id",
                     li."id"
        """

        cursor.execute(query, {"today": today})

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
                        "lease_id": row["lease_id"],
                        "start_date": row["start_date"],
                        "end_date": row["end_date"],
                        "note": str(shares_total),
                    }
                )

        return data

    def get_data(self, input_data):
        today = datetime.date.today()

        result = []
        with connection.cursor() as cursor:
            for lease_list_type in InvoicingReviewSection:
                result.append(
                    {
                        "section": lease_list_type.value,
                        "lease_id": None,
                        "start_date": None,
                        "end_date": None,
                    }
                )

                rows = []
                if lease_list_type.value in INVOICING_REVIEW_QUERIES:
                    cursor.execute(
                        INVOICING_REVIEW_QUERIES[lease_list_type.value],
                        {"today": today},
                    )
                    rows = dictfetchall(cursor)

                if hasattr(self, f"get_{lease_list_type.value}_data"):
                    rows = getattr(self, f"get_{lease_list_type.value}_data")(cursor)

                rows.sort(key=itemgetter("lease_id"))
                result.extend(rows)

        return result

    def get_response(self, request):
        report_data = self.get_data(self.get_input_data(request))
        serialized_report_data = self.serialize_data(report_data)

        if request.accepted_renderer.format != "xlsx":
            return Response(serialized_report_data)

        final_report_data = []
        for datum in serialized_report_data:
            if not datum["section"]:
                final_report_data.append(datum)
                continue

            section = InvoicingReviewSection(datum["section"])

            final_report_data.append(ExcelRow())

            # Intermediate heading: name of section
            final_report_data.append(
                ExcelRow(
                    [
                        ExcelCell(
                            column=0,
                            value=str(section.label),
                            format_type=FormatType.BOLD,
                        )
                    ]
                )
            )

            # Field labels as reminders under each section heading
            row = []
            for i, key in enumerate(self.output_fields):
                if key == "section":
                    continue
                row.append(
                    ExcelCell(
                        column=i,
                        value=str(self.output_fields[key]["label"]),
                        format_type=FormatType.BOLD,
                    )
                )

            final_report_data.append(ExcelRow(row))

        return Response(final_report_data)
