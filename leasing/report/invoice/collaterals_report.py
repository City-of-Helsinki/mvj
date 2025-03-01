from django import forms
from django.utils.translation import gettext_lazy as _

from leasing.models import Collateral, CollateralType, ServiceUnit
from leasing.report.lease.common_getters import LeaseLinkData
from leasing.report.report_base import ReportBase


def get_lease_link_data_from_collateral(collateral: Collateral) -> LeaseLinkData:
    try:
        return {
            "id": collateral.contract.lease.id,
            "identifier": collateral.contract.lease.get_identifier_string(),
        }
    except AttributeError:
        return {
            "id": None,
            "identifier": None,
        }


def get_start_date(obj):
    if not obj.contract.lease:
        return

    return obj.contract.lease.start_date


def get_end_date(obj):
    if not obj.contract.lease:
        return

    return obj.contract.lease.end_date


class CollateralsReport(ReportBase):
    name = _("Collaterals")
    description = _("Show all collaterals")
    slug = "collaterals"
    input_fields = {
        "service_unit": forms.ModelMultipleChoiceField(
            label=_("Service unit"),
            queryset=ServiceUnit.objects.all(),
            required=False,
        ),
        "collateral_type": forms.ModelChoiceField(
            label=_("Type"),
            queryset=CollateralType.objects.all(),
            empty_label=None,
            required=False,
        ),
        "paid": forms.NullBooleanField(label=_("Paid"), required=False),
        "returned": forms.NullBooleanField(label=_("Returned"), required=False),
    }
    output_fields = {
        "lease_identifier": {
            "source": get_lease_link_data_from_collateral,
            "label": _("Lease id"),
        },
        "start_date": {
            "source": get_start_date,
            "label": _("Lease start date"),
            "format": "date",
        },
        "end_date": {
            "source": get_end_date,
            "label": _("Lease end date"),
            "format": "date",
        },
        "total_amount": {"label": _("Total amount"), "format": "money", "width": 13},
        "paid_date": {"label": _("Paid date"), "format": "date"},
        "returned_date": {"label": _("Returned date"), "format": "date"},
        "note": {"label": _("Note"), "width": 50},
    }

    def get_data(self, input_data):
        qs = (
            Collateral.objects.all()
            .select_related(
                "contract",
                "contract__lease",
                "contract__lease__identifier",
                "contract__lease__identifier__type",
                "contract__lease__identifier__district",
                "contract__lease__identifier__municipality",
            )
            .order_by(
                "contract__lease__identifier__type__identifier",
                "contract__lease__identifier__municipality__identifier",
                "contract__lease__identifier__district__identifier",
                "contract__lease__identifier__sequence",
            )
        )

        if input_data["service_unit"]:
            qs = qs.filter(contract__lease__service_unit__in=input_data["service_unit"])

        if input_data["collateral_type"]:
            qs = qs.filter(type=input_data["collateral_type"])

        if input_data["paid"] is not None:
            qs = qs.filter(paid_date__isnull=not input_data["paid"])

        if input_data["returned"] is not None:
            qs = qs.filter(returned_date__isnull=not input_data["returned"])

        return qs
