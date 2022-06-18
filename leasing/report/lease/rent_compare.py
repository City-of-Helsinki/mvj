import datetime
from decimal import Decimal

from django import forms
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

from leasing.models import Lease
from leasing.report.report_base import AsyncReportBase


class RentCompareReport(AsyncReportBase):
    name = _("Rent compare")
    description = _("Show difference in rent between two years")
    slug = "rent_compare"
    input_fields = {
        "first_year": forms.IntegerField(
            label=_("First year"), required=True, min_value=1900, max_value=3000
        ),
        "second_year": forms.IntegerField(
            label=_("Second year"), required=True, min_value=1900, max_value=3000
        ),
    }
    output_fields = {
        "lease_id": {"label": _("Lease identifier"), "width": 13},
        "first_year": {"label": _("First year rent"), "format": "money", "width": 13},
        "second_year": {"label": _("Second year rent"), "format": "money", "width": 13},
        "difference": {"label": _("Difference percent"), "format": "percentage"},
    }
    async_task_timeout = 60 * 30  # 30 minutes

    def get_data(self, input_data):  # NOQA C901
        first_year = input_data["first_year"]
        second_year = input_data["second_year"]

        first_year_start_date = datetime.date(year=first_year, month=1, day=1)
        first_year_end_date = datetime.date(year=first_year, month=12, day=31)
        second_year_start_date = datetime.date(year=second_year, month=1, day=1)
        second_year_end_date = datetime.date(year=second_year, month=12, day=31)

        leases = (
            Lease.objects.filter(
                (
                    (
                        Q(start_date__isnull=True)
                        | Q(start_date__lte=first_year_end_date)
                    )
                    & (
                        Q(end_date__isnull=True)
                        | Q(end_date__gte=first_year_start_date)
                    )
                )
                | (
                    (
                        Q(start_date__isnull=True)
                        | Q(start_date__lte=second_year_end_date)
                    )
                    & (
                        Q(end_date__isnull=True)
                        | Q(end_date__gte=second_year_start_date)
                    )
                )
            )
            .filter(
                (
                    (
                        Q(rents__start_date__isnull=True)
                        | Q(rents__start_date__lte=first_year_end_date)
                    )
                    & (
                        Q(rents__end_date__isnull=True)
                        | Q(rents__end_date__gte=first_year_start_date)
                    )
                )
                | (
                    (
                        Q(rents__start_date__isnull=True)
                        | Q(rents__start_date__lte=second_year_end_date)
                    )
                    & (
                        Q(rents__end_date__isnull=True)
                        | Q(rents__end_date__gte=second_year_start_date)
                    )
                )
            )
            .order_by(
                "identifier__type__identifier",
                "identifier__municipality__identifier",
                "identifier__district__identifier",
                "identifier__sequence",
            )
        )

        results = []
        for lease in leases:
            result = {
                "lease_id": lease.get_identifier_string(),
                "first_year": None,
                "second_year": None,
                "difference": None,
            }

            for year in [first_year, second_year]:
                year_key = "first_year" if year == first_year else "second_year"
                try:
                    rent_amount = lease.calculate_rent_amount_for_year(year)

                    result[year_key] = rent_amount.get_total_amount()
                except NotImplementedError:
                    # Ignore the rent if the rent doesn't have an index defined
                    pass

            if result["first_year"] and result["second_year"]:
                difference = abs(result["second_year"] - result["first_year"])
                result["difference"] = difference / result["first_year"] * Decimal(100)
                if result["first_year"] > result["second_year"]:
                    result["difference"] = -result["difference"]

            results.append(result)

        return results
