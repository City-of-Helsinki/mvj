from django import forms
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from enumfields.drf import EnumField

from leasing.enums import RentAdjustmentAmountType, RentAdjustmentType, SubventionType
from leasing.models import RentAdjustment
from leasing.report.report_base import ReportBase
from leasing.models import ServiceUnit


def get_lease_id(obj):
    return obj.rent.lease.get_identifier_string()


def get_intended_use(obj):
    return obj.intended_use.name


def get_management_subventions(obj):
    items = []
    for management_subvention in obj.management_subventions.all():
        items.append(
            f"{management_subvention.management.name} {management_subvention.subvention_amount}%"
        )

    return ", ".join(items)


def get_temporary_subventions(obj):
    items = []
    for temporary_subvention in obj.temporary_subventions.all():
        items.append(
            f"{temporary_subvention.description} {temporary_subvention.subvention_percent}%"
        )

    return ", ".join(items)


class RentAdjustmentsReport(ReportBase):
    name = _("Rent adjustments")
    description = _("Shows all of the rent adjustments")
    slug = "rent_adjustments"
    input_fields = {
        "service_unit": forms.ModelChoiceField(
            label=_("Palvelukokonaisuus"), required=False, queryset=ServiceUnit.objects.all()
        )
    }
    output_fields = {
        "lease_id": {"source": get_lease_id, "label": _("Lease id")},
        "type": {
            "label": _("Type"),
            "serializer_field": EnumField(enum=RentAdjustmentType),
        },
        "intended_use": {"source": get_intended_use, "label": _("Intended use")},
        "start_date": {"label": _("Start date"), "format": "date"},
        "end_date": {"label": _("End date"), "format": "date"},
        "full_amount": {"label": _("Full amount")},
        "amount_type": {
            "label": _("Amount type"),
            "serializer_field": EnumField(enum=RentAdjustmentAmountType),
        },
        "amount_left": {"label": _("Amount left"), "format": "money"},
        "subvention_type": {
            "label": _("Subvention type"),
            "serializer_field": EnumField(enum=SubventionType),
            "width": 15,
        },
        "subvention_base_percent": {
            "label": _("Subvention base percent"),
            "format": "percent",
        },
        "subvention_graduated_percent": {
            "label": _("Graduated subvention percent"),
            "format": "percent",
        },
        "management_subvention": {
            "source": get_management_subventions,
            "label": _("Management subventions"),
            "width": 30,
        },
        "temporary_subvention": {
            "source": get_temporary_subventions,
            "label": _("Temporary subventions"),
            "width": 30,
        },
        "note": {"label": _("Note"), "width": 60},
    }

    def get_data(self, input_data):
        today = timezone.now().date()

        qs = (
            RentAdjustment.objects.filter(
                Q(end_date__isnull=True) | Q(end_date__gte=today),
                Q(rent__lease__end_date__isnull=True)
                | Q(rent__lease__end_date__gte=today),
            )
            .select_related(
                "intended_use",
                "rent__lease",
                "rent__lease__identifier",
                "rent__lease__identifier__type",
                "rent__lease__identifier__district",
                "rent__lease__identifier__municipality",
                "rent__lease__municipality",
            )
            .prefetch_related(
                "management_subventions",
                "management_subventions__management",
                "temporary_subventions",
            )
            .order_by(
                "rent__lease__identifier__municipality__identifier",
                "rent__lease__identifier__type__identifier",
                "rent__lease__identifier__district__identifier",
                "rent__lease__identifier__sequence",
            )
        )

        if input_data["service_unit"] is not None and input_data["service_unit"].id:
            qs = qs.filter(rent__lease__service_unit=input_data["service_unit"].id)

        return qs
