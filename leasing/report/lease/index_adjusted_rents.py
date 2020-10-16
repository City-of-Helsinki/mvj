from decimal import Decimal

from django import forms
from django.utils.translation import ugettext_lazy as _

from leasing.models import IndexAdjustedRent
from leasing.report.report_base import ReportBase


class IndexAdjustedRentChangeReport(ReportBase):
    name = _("Index adjusted rent change")
    description = _(
        "The percentual change of index adjusted rents between specified years"
    )
    slug = "index_adjusted_rent_change"
    input_fields = {
        "year1": forms.IntegerField(label=_("Year 1"), required=True),
        "year2": forms.IntegerField(label=_("Year 2"), required=True),
    }
    output_fields = {
        "lease_id": {"label": _("Lease id")},
        "index_type": {"label": _("Index type")},
        "intended_use": {"label": _("Intended use")},
        "year1_rent_start_date": {
            "label": _("Year1 index adjusted rent start date"),
            "format": "date",
        },
        "year1_rent_end_date": {
            "label": _("Year1 index adjusted rent end date"),
            "format": "date",
        },
        "year1_rent": {"label": _("Year 1 rent"), "format": "money"},
        "year1_factor": {"label": _("Year 1 factor")},
        "year2_rent_start_date": {
            "label": _("Year2 index adjusted rent start date"),
            "format": "date",
        },
        "year2_rent_end_date": {
            "label": _("Year2 index adjusted rent end date"),
            "format": "date",
        },
        "year2_rent": {"label": _("Year 2 rent"), "format": "money"},
        "year2_factor": {"label": _("Year 2 factor")},
        "pc_change": {"label": _("Percentual change")},
    }

    def get_data(self, input_data):
        year1 = input_data["year1"]
        year2 = input_data["year2"]
        year1_index_adjusted_rent_qs = (
            IndexAdjustedRent.objects.filter(start_date__year=year1)
            .select_related(
                "intended_use",
                "rent",
                "rent__lease",
                "rent__lease__identifier",
                "rent__lease__identifier__type",
                "rent__lease__identifier__district",
                "rent__lease__identifier__municipality",
            )
            .prefetch_related(
                "rent__index_adjusted_rents", "rent__index_adjusted_rents__intended_use"
            )
        )
        aggregated_data = []
        for year1_iar in year1_index_adjusted_rent_qs:
            for iar in year1_iar.rent.index_adjusted_rents.all():
                # Iterate instead of filter() to ensure use of prefetch
                if iar.end_date.year != year2:
                    continue
                if iar.intended_use != year1_iar.intended_use:
                    continue

                # Don't divide by 0
                if iar.amount == Decimal(0) or year1_iar.amount == Decimal(0):
                    change = None
                else:
                    change = round(((iar.amount / year1_iar.amount) * 100) - 100, 2)

                aggregated_data.append(
                    {
                        "lease_id": year1_iar.rent.lease.get_identifier_string(),
                        "index_type": str(year1_iar.rent.index_type),
                        "intended_use": year1_iar.intended_use.name,
                        "year1_rent_start_date": year1_iar.start_date,
                        "year1_rent_end_date": year1_iar.end_date,
                        "year1_rent": year1_iar.amount,
                        "year1_factor": year1_iar.factor,
                        "year2_rent_start_date": iar.start_date,
                        "year2_rent_end_date": iar.end_date,
                        "year2_rent": iar.amount,
                        "year2_factor": iar.factor,
                        "pc_change": change,
                    }
                )
        return aggregated_data
