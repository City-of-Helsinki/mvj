from typing import Any

from django import forms
from django.db.models import Q, QuerySet
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from leasing.enums import IndexType, TenantContactType
from leasing.models import Rent, ServiceUnit
from leasing.report.excel import FormatType
from leasing.report.lease.common_getters import get_lease_link_data_from_related_object
from leasing.report.report_base import ReportBase


def get_tenants(rent: Rent) -> str:
    today = timezone.now().date()
    contacts = set()
    for tenant in rent.lease.tenants.all():
        for tc in tenant.tenantcontact_set.all():
            if tc.type != TenantContactType.TENANT:
                continue
            if (tc.end_date is None or tc.end_date >= today) and (
                tc.start_date is None or tc.start_date <= today
            ):
                contacts.add(tc.contact)
    return ", ".join([c.get_name() for c in contacts])


def get_area_id(rent: Rent) -> str:
    return ", ".join(
        [la.identifier for la in rent.lease.lease_areas.all() if la.archived_at is None]
    )


def get_contract_number(rent: Rent) -> str:
    contract_numbers = []
    for contract in rent.lease.contracts.all():
        if not contract.contract_number:
            continue
        contract_numbers.append(contract.contract_number)
    return " / ".join(contract_numbers)


def get_area_address(rent: Rent) -> str:
    addresses = []
    for lease_area in rent.lease.lease_areas.all():
        if lease_area.archived_at:
            continue
        for area_address in lease_area.addresses.all():
            if not area_address.is_primary:
                continue
            addresses.append(area_address.address)
    return ", ".join(addresses)


def get_municipality(rent: Rent) -> str:
    return rent.lease.municipality.name


def get_start_date(rent: Rent) -> str:
    return rent.lease.start_date


def get_end_date(rent: Rent) -> str:
    return rent.lease.end_date


def get_intended_use(rent: Rent) -> str:
    iu = rent.lease.intended_use
    return iu.name if iu else "-"


def get_index_type(rent: Rent) -> str:
    return str(rent.index_type.label)


class IndexTypesReport(ReportBase):
    name = _("Index type leases")
    description = _("Show leases with a certain index type")
    slug = "index_types"
    input_fields = {
        "service_unit": forms.ModelMultipleChoiceField(
            label=_("Service unit"),
            queryset=ServiceUnit.objects.all(),
            required=False,
        ),
        "index_type": forms.ChoiceField(
            label=_("Index type"), required=True, choices=IndexType.choices()
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
        },
        "tenant_name": {"source": get_tenants, "label": _("Tenant name"), "width": 50},
        "lease_area_identifier": {
            "source": get_area_id,
            "label": _("Lease area identifier"),
            "width": 50,
        },
        "area_address": {
            "source": get_area_address,
            "label": _("Address"),
            "width": 50,
        },
        "municipality": {"source": get_municipality, "label": _("Municipality")},
        "contract_number": {
            "source": get_contract_number,
            "label": _("Contract number"),
            "is_numeric": True,
        },
        "start_date": {
            "source": get_start_date,
            "label": _("Start date"),
            "format": FormatType.DATE.value,
        },
        "end_date": {
            "source": get_end_date,
            "label": _("End date"),
            "format": FormatType.DATE.value,
        },
        "intended_use": {"source": get_intended_use, "label": _("Intended use")},
        "index_type": {"source": get_index_type, "label": _("Index type")},
    }

    def get_data(self, input_data: dict[str, Any]) -> QuerySet:
        qs = (
            Rent.objects.filter(
                index_type=input_data["index_type"], lease__deleted__isnull=True
            )
            .select_related(
                "lease",
                "lease__identifier",
                "lease__identifier__type",
                "lease__identifier__district",
                "lease__identifier__municipality",
                "lease__municipality",
                "lease__intended_use",
            )
            .prefetch_related(
                "lease__tenants",
                "lease__tenants__tenantcontact_set",
                "lease__tenants__tenantcontact_set__contact",
                "lease__lease_areas",
                "lease__lease_areas__addresses",
                "lease__contracts",
            )
            .order_by(
                "lease__identifier__municipality__identifier",
                "lease__identifier__type__identifier",
                "lease__identifier__district__identifier",
                "lease__identifier__sequence",
            )
        )

        if input_data["service_unit"]:
            qs = qs.filter(lease__service_unit__in=input_data["service_unit"])

        if input_data["only_active_leases"]:
            qs = qs.filter(
                Q(lease__end_date__isnull=True)
                | Q(lease__end_date__gte=timezone.now().date())
            )
        return qs
