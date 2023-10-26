import datetime

from django import forms
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

from leasing.enums import RentType, TenantContactType
from leasing.models import Rent, ServiceUnit
from leasing.report.report_base import ReportBase

def get_lease_id(obj):
    return obj.lease.get_identifier_string()


def get_tenants(obj):
    today = datetime.date.today()
    contacts = set()
    for tenant in obj.lease.tenants.all():
        for tc in tenant.tenantcontact_set.all():
            if tc.type != TenantContactType.TENANT:
                continue
            if (tc.end_date is None or tc.end_date >= today) and (
                tc.start_date is None or tc.start_date <= today
            ):
                contacts.add(tc.contact)
    return ", ".join([c.get_name() for c in contacts])


def get_area_id(obj):
    return ", ".join(
        [la.identifier for la in obj.lease.lease_areas.all() if la.archived_at is None]
    )


def get_contract_number(obj):
    contract_numbers = []
    for contract in obj.lease.contracts.all():
        if not contract.contract_number:
            continue
        contract_numbers.append(contract.contract_number)
    return " / ".join(contract_numbers)


def get_area_address(obj):
    addresses = []
    for lease_area in obj.lease.lease_areas.all():
        if lease_area.archived_at:
            continue
        for area_address in lease_area.addresses.all():
            if not area_address.is_primary:
                continue
            addresses.append(area_address.address)
    return ", ".join(addresses)


def get_municipality(obj):
    return obj.lease.municipality.name


def get_start_date(obj):
    return obj.lease.start_date


def get_end_date(obj):
    return obj.lease.end_date


def get_intended_use(obj):
    iu = obj.lease.intended_use
    return iu.name if iu else "-"


def get_rent_type(obj):
    return str(obj.type.label)


class RentTypeReport(ReportBase):
    name = _("Rent type leases")
    description = _("Show leases with a certain rent type")
    slug = "rent_type"
    input_fields = {
        "service_unit": forms.ModelChoiceField(
            label=_("Palvelukokonaisuus"), required=False, queryset=ServiceUnit.objects.all()
        ),
        "rent_type": forms.ChoiceField(
            label=_("Rent type"), required=True, choices=RentType.choices()
        ),
        "only_active_leases": forms.BooleanField(
            label=_("Only active leases"), required=False
        ),
    }
    output_fields = {
        "lease_id": {"source": get_lease_id, "label": _("Lease id")},
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
            "format": "date",
        },
        "end_date": {"source": get_end_date, "label": _("End date"), "format": "date"},
        "intended_use": {"source": get_intended_use, "label": _("Intended use")},
        "rent_type": {"source": get_rent_type, "label": _("Rent type")},
    }

    def get_data(self, input_data):
        qs = (
            Rent.objects.filter(
                type=input_data["rent_type"], lease__deleted__isnull=True
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

        if input_data["only_active_leases"]:
            qs = qs.filter(
                Q(lease__end_date__isnull=True)
                | Q(lease__end_date__gte=datetime.date.today())
            )
        if input_data["service_unit"] is not None and input_data["service_unit"].id:
            qs = qs.filter(Q(lease__service_unit=input_data["service_unit"].id))


        return qs
