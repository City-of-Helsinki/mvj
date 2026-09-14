from typing import Any

from django import forms
from django.db.models import Q, QuerySet
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from enumfields.drf import EnumField

from leasing.enums import AreaUnit, BasisOfRentType, BasisOfRentZone, SubventionType
from leasing.models import LeaseBasisOfRent, ServiceUnit
from leasing.report.excel import FormatType
from leasing.report.lease.common_getters import get_lease_link_data_from_related_object
from leasing.report.report_base import ReportBase


def get_intended_use(basis_of_rent: LeaseBasisOfRent) -> str:
    return basis_of_rent.intended_use.name


def get_lease_intended_use(basis_of_rent: LeaseBasisOfRent) -> str:
    return (
        basis_of_rent.lease.intended_use.name
        if basis_of_rent.lease.intended_use
        else ""
    )


def get_service_unit(basis_of_rent: LeaseBasisOfRent) -> str:
    return basis_of_rent.lease.service_unit.name


def is_lease_active(basis_of_rent: LeaseBasisOfRent) -> bool:
    # future start dates are also considered active
    end_date = basis_of_rent.lease.end_date
    return end_date is None or end_date >= timezone.now().date()


def get_index(basis_of_rent: LeaseBasisOfRent) -> str:
    return str(basis_of_rent.index) if basis_of_rent.index else ""


def get_index_adjusted_amount_per_area(
    basis_of_rent: LeaseBasisOfRent,
):
    return basis_of_rent.get_index_adjusted_amount_per_area()


def get_initial_year_rent(basis_of_rent: LeaseBasisOfRent):
    return basis_of_rent.calculate_initial_year_rent()


def get_discounted_rent(basis_of_rent: LeaseBasisOfRent):
    return basis_of_rent.calculate_discounted_rent()


def get_subvented_initial_year_rent(basis_of_rent: LeaseBasisOfRent):
    return basis_of_rent.calculate_subvented_initial_year_rent()


def get_subvention_euros_per_year(basis_of_rent: LeaseBasisOfRent):
    return basis_of_rent.calculate_subvention_euros_per_year()


def get_subvention_percent(basis_of_rent: LeaseBasisOfRent):
    return basis_of_rent.calculate_subvention_percent()


def get_subvention_amount_per_area(basis_of_rent: LeaseBasisOfRent):
    return basis_of_rent.calculate_subvention_amount_per_area()


def get_temporary_subvention_percentage(basis_of_rent: LeaseBasisOfRent):
    return basis_of_rent.calculate_temporary_subvention_percentage()


def get_temporary_discount_amount_euros_per_year(
    basis_of_rent: LeaseBasisOfRent,
):
    return basis_of_rent.calculate_temporary_subvention_data()[
        "total_amount_euros_per_year"
    ]


class LeaseBasisOfRentReport(ReportBase):
    name = _("Lease bases of rent")
    description = _("Shows lease bases of rent")
    slug = "lease_basis_of_rent"
    input_fields = {
        "service_unit": forms.ModelMultipleChoiceField(
            label=_("Service unit"),
            queryset=ServiceUnit.objects.all(),
            required=False,
        ),
        "only_active_leases": forms.BooleanField(
            label=_("Only active leases"), required=False
        ),
    }
    output_fields = {
        "lease_identifier": {
            "source": get_lease_link_data_from_related_object,
            "label": _("Lease id"),
            "format": FormatType.URL.value,
            "width": 13,
        },
        "lease_intended_use": {
            "source": get_lease_intended_use,
            "label": _("Lease intended use"),
            "width": 25,
        },
        "service_unit": {
            "source": get_service_unit,
            "label": _("Service unit"),
            "width": 25,
        },
        "is_lease_active": {
            "source": is_lease_active,
            "label": _("Active lease"),
            "format": FormatType.BOOLEAN.value,
        },
        "type": {
            "label": _("Type"),
            "serializer_field": EnumField(enum=BasisOfRentType),
        },
        "intended_use": {
            "source": get_intended_use,
            "label": _("Intended use"),
            "width": 25,
        },
        "area": {"label": _("Area amount"), "format": FormatType.NUMBER.value},
        "zone": {
            "label": _("Zone"),
            "serializer_field": EnumField(enum=BasisOfRentZone, allow_null=True),
        },
        "area_unit": {
            "label": _("Area unit"),
            "serializer_field": EnumField(enum=AreaUnit),
        },
        "amount_per_area": {
            "source": get_index_adjusted_amount_per_area,
            "label": _("Unit price (index)"),
            "format": FormatType.MONEY.value,
        },
        "index": {"source": get_index, "label": _("Index"), "width": 20},
        "profit_margin_percentage": {
            "label": _("Profit margin percentage"),
            "format": FormatType.PERCENTAGE.value,
        },
        "discount_percentage": {
            "label": _("Discount percentage"),
            "format": FormatType.PERCENTAGE.value,
        },
        "initial_year_rent": {
            "source": get_initial_year_rent,
            "label": _("Initial year rent"),
            "format": FormatType.MONEY.value,
        },
        "discounted_rent": {
            "source": get_discounted_rent,
            "label": _("Discounted rent"),
            "format": FormatType.MONEY.value,
        },
        "subvention_type": {
            "label": _("Subvention type"),
            "serializer_field": EnumField(enum=SubventionType, allow_null=True),
        },
        "subvention_base_percent": {
            "label": _("Subvention base percent"),
            "format": FormatType.PERCENTAGE.value,
        },
        "subvention_graduated_percent": {
            "label": _("Subvention graduated percent"),
            "format": FormatType.PERCENTAGE.value,
        },
        "subvented_initial_year_rent": {
            "source": get_subvented_initial_year_rent,
            "label": _("Subvented initial year rent"),
            "format": FormatType.MONEY.value,
        },
        "subvention_euros_per_year": {
            "source": get_subvention_euros_per_year,
            "label": _("Subvention euros per year"),
            "format": FormatType.MONEY.value,
        },
        "subvention_percent": {
            "source": get_subvention_percent,
            "label": _("Subvention percent"),
            "format": FormatType.PERCENTAGE.value,
        },
        "subvention_amount_per_area": {
            "source": get_subvention_amount_per_area,
            "label": _("Subvention amount per area"),
            "format": FormatType.MONEY.value,
        },
        "temporary_subvention_percentage": {
            "source": get_temporary_subvention_percentage,
            "label": _("Temporary subvention percentage"),
            "format": FormatType.PERCENTAGE.value,
        },
        "temporary_discount_amount_euros_per_year": {
            "source": get_temporary_discount_amount_euros_per_year,
            "label": _("Temporary discount amount euros per year"),
            "format": FormatType.MONEY.value,
        },
    }

    def get_data(self, input_data: dict[str, Any]) -> QuerySet:
        current_date = timezone.now().date()
        queryset = (
            LeaseBasisOfRent.objects.filter(
                lease__deleted__isnull=True,
                archived_at__isnull=True,
                locked_at__isnull=False,
            )
            .select_related(
                "lease",
                "lease__identifier",
                "lease__identifier__type",
                "lease__identifier__district",
                "lease__identifier__municipality",
                "lease__intended_use",
                "lease__service_unit",
                "intended_use",
                "index",
                "plans_inspected_by",
                "locked_by",
            )
            .prefetch_related(
                "management_subventions__management",
                "temporary_subventions",
            )
            .order_by(
                "lease__identifier__municipality__identifier",
                "lease__identifier__type__identifier",
                "lease__identifier__district__identifier",
                "lease__identifier__sequence",
                "id",
            )
        )

        if input_data["service_unit"]:
            queryset = queryset.filter(
                lease__service_unit__in=input_data["service_unit"]
            )

        if input_data["only_active_leases"]:
            # future start dates are also considered active
            queryset = queryset.filter(
                Q(lease__end_date__isnull=True) | Q(lease__end_date__gte=current_date)
            )

        return queryset
