import datetime
from collections import defaultdict
from decimal import ROUND_HALF_UP, Decimal

from django import forms
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from leasing.enums import LeaseState
from leasing.models import Lease
from leasing.report.excel import (
    ExcelCell,
    ExcelRow,
    FormatType,
    PreviousRowsSumCell,
    SumCell,
)
from leasing.report.report_base import AsyncReportBase

INTERNAL_LEASE_TYPES = [
    "K0",
    "V1",
    "V4",
    "Y0",
    "Y1",
    "Y2",
    "Y3",
    "Y4",
    "Y5",
    "Y6",
    "Y7",
    "Y8",
    "Y9",
]


class RentForecastReport(AsyncReportBase):
    name = _("Rent forecast")
    description = _("Calculate total yearly rent by lease type")
    slug = "rent_forecast"
    input_fields = {
        "start_year": forms.IntegerField(
            label=_("Start year"), required=True, min_value=2020, max_value=2050
        ),
        "end_year": forms.IntegerField(
            label=_("End year"), required=True, min_value=2021, max_value=2050
        ),
    }
    output_fields = {
        "lease_type": {"label": _("Lease type")},
        "year": {"label": _("Year")},
        "rent": {"label": _("Rent"), "format": "money", "width": 13},
    }

    def get_data(self, input_data):  # NOQA C901
        start_date = datetime.date(year=input_data["start_year"], month=1, day=1)
        end_date = datetime.date(year=input_data["end_year"], month=12, day=31)

        leases = (
            Lease.objects.filter(
                (Q(start_date__isnull=True) | Q(start_date__lte=end_date))
                & (Q(end_date__isnull=True) | Q(end_date__gte=start_date))
            )
            .filter(
                state__in=[
                    LeaseState.LEASE,
                    LeaseState.SHORT_TERM_LEASE,
                    LeaseState.LONG_TERM_LEASE,
                    LeaseState.RYA,
                ]
            )
            .select_related("type")
        )

        years = range(input_data["start_year"], input_data["end_year"] + 1)

        rent_sums = {
            "internal": defaultdict(lambda: defaultdict(Decimal)),
            "external": defaultdict(lambda: defaultdict(Decimal)),
        }

        for lease in leases:
            # Katja:
            # Y9-alkuisista pitäisi jättää pois ne vuokraukset, joiden tyyppi on RYA.
            if lease.state == LeaseState.RYA and lease.type.identifier == "Y9":
                continue

            for year in years:
                try:
                    rent_amount = lease.calculate_rent_amount_for_year(year)

                    rent_sums_key = "external"
                    if lease.type.identifier in INTERNAL_LEASE_TYPES:
                        rent_sums_key = "internal"

                    rent_sums[rent_sums_key][year][
                        lease.type.identifier
                    ] += rent_amount.get_total_amount()
                except NotImplementedError:
                    # Ignore the rent if the rent doesn't have an index defined
                    pass

        result = []
        data_row_num = 0

        for year in years:
            totals_row_nums = []

            for rent_sums_key in ["internal", "external"]:
                # Spelled out here for the makemessages to pick them up
                if rent_sums_key == "internal":
                    internal_external_text = _("Internal")
                else:
                    internal_external_text = _("External")

                row_count = 0
                for lease_type, total_rent_amount in sorted(
                    rent_sums[rent_sums_key][year].items()
                ):
                    result.append(
                        {
                            "lease_type": lease_type,
                            "year": year,
                            "rent": Decimal(total_rent_amount).quantize(
                                Decimal(".01"), rounding=ROUND_HALF_UP
                            ),
                        }
                    )
                    row_count += 1
                    data_row_num += 1

                total_row = ExcelRow(
                    [
                        ExcelCell(
                            column=0,
                            value=str(
                                _("Total {year} {internal_external_text}").format(
                                    year=year,
                                    internal_external_text=internal_external_text,
                                )
                            ),
                            format_type=FormatType.BOLD,
                        ),
                        PreviousRowsSumCell(
                            column=2, count=row_count, format_type=FormatType.BOLD_MONEY
                        ),
                    ]
                )

                result.append(total_row)
                totals_row_nums.append(data_row_num)
                data_row_num += 1

                result.append(ExcelRow())
                data_row_num += 1

            year_total_row = ExcelRow()
            year_total_row.cells.append(
                ExcelCell(
                    column=0,
                    value="{} {}".format(str(_("Total")), year),
                    format_type=FormatType.BOLD,
                )
            )

            year_total_rent_sum_cell = SumCell(
                column=2, format_type=FormatType.BOLD_MONEY
            )
            for totals_row_num in totals_row_nums:
                year_total_rent_sum_cell.add_target_range(
                    (totals_row_num, 2, totals_row_num, 2)
                )

            year_total_row.cells.append(year_total_rent_sum_cell)
            result.append(year_total_row)
            data_row_num += 1

            result.append(ExcelRow())
            data_row_num += 1

        return result
