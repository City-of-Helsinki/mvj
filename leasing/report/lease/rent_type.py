import datetime
from typing import Protocol

from django import forms
from django.db.models import CharField, Q
from django.db.models.expressions import RawSQL
from django.utils.translation import gettext_lazy as _

from leasing.enums import ContactType, RentType, TenantContactType
from leasing.models import Rent, ServiceUnit
from leasing.report.lease.common_getters import get_lease_ids_from_related_object
from leasing.report.report_base import ReportBase


class RentWithContactNames(Protocol):
    contact_names: str


def get_tenants(obj: RentWithContactNames) -> str:
    return obj.contact_names


def get_area_id(obj: Rent):
    return ", ".join(
        [la.identifier for la in obj.lease.lease_areas.all() if la.archived_at is None]
    )


def get_contract_number(obj: Rent):
    contract_numbers = []
    for contract in obj.lease.contracts.all():
        if not contract.contract_number:
            continue
        contract_numbers.append(contract.contract_number)
    return " / ".join(contract_numbers)


def get_area_address(obj: Rent):
    addresses = []
    for lease_area in obj.lease.lease_areas.all():
        if lease_area.archived_at:
            continue
        for area_address in lease_area.addresses.all():
            if not area_address.is_primary:
                continue
            addresses.append(area_address.address)
    return ", ".join(addresses)


def get_municipality(obj: Rent):
    return obj.lease.municipality.name


def get_start_date(obj: Rent):
    return obj.lease.start_date


def get_end_date(obj: Rent):
    return obj.lease.end_date


def get_intended_use(obj: Rent):
    iu = obj.lease.intended_use
    return iu.name if iu else "-"


def get_rent_type(obj: Rent):
    return str(obj.type.label)


class RentTypeReport(ReportBase):
    name = _("Rent type leases")
    description = _("Show leases with a certain rent type")
    slug = "rent_type"
    input_fields = {
        "service_unit": forms.ModelMultipleChoiceField(
            label=_("Service unit"),
            queryset=ServiceUnit.objects.all(),
            required=False,
        ),
        "rent_type": forms.ChoiceField(
            label=_("Rent type"), required=True, choices=RentType.choices()
        ),
        "only_active_leases": forms.BooleanField(
            label=_("Only active leases"), required=False
        ),
    }
    output_fields = {
        "lease_ids": {
            "source": get_lease_ids_from_related_object,
            "label": _("Lease id"),
        },
        "tenant_name": {
            "source": get_tenants,
            "label": _("Tenant name"),
            "width": 50,
        },
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
        current_date = datetime.date.today()
        # RawSQL is used in order to make the report load faster, it was and still is extremely slow with 10k+ entries
        # This SQL uses PostgreSQL expression STRING_AGG to concatenate contact names into a single string
        # The CASE statement is used to to select the name in SQL instead of doing it in Django
        contact_names_concat_sql = """
        SELECT STRING_AGG(contact_name, ', ' ORDER BY contact_name)
        FROM (
            SELECT DISTINCT
                CASE
                    WHEN leasing_contact.type = %s
                        THEN leasing_contact.first_name || ' ' || leasing_contact.last_name
                    ELSE leasing_contact.name
                END AS contact_name
            FROM leasing_contact
            JOIN leasing_tenantcontact ON leasing_tenantcontact.contact_id = leasing_contact.id
            JOIN leasing_tenant ON leasing_tenantcontact.tenant_id = leasing_tenant.id
            WHERE
                leasing_tenant.lease_id = leasing_rent.lease_id
                AND leasing_tenantcontact.type = %s
                AND (leasing_tenantcontact.start_date IS NULL OR leasing_tenantcontact.start_date <= %s)
                AND (leasing_tenantcontact.end_date IS NULL OR leasing_tenantcontact.end_date >= %s)
        ) AS distinct_contacts
        """
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
                "lease__lease_areas",
                "lease__lease_areas__addresses",
                "lease__contracts",
            )
            .annotate(
                contact_names=RawSQL(
                    sql=contact_names_concat_sql,
                    params=(
                        ContactType.PERSON.value,
                        TenantContactType.TENANT.value,
                        current_date,
                        current_date,
                    ),
                    output_field=CharField(),
                )
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
                Q(lease__end_date__isnull=True) | Q(lease__end_date__gte=current_date)
            )

        return qs
