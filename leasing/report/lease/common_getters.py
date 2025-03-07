import datetime
from typing import Protocol, TypedDict

from django.db.models import QuerySet

from leasing.enums import TenantContactType
from leasing.models import Contract
from leasing.models.lease import Lease

RE_LEASE_DECISION_TYPE_ID = 29  # Vuokraus (sopimuksen uusiminen/jatkam.)

OPTION_TO_PURCHASE_CONDITION_TYPE_ID = 24  # 24 = Osto-optioehto


class LeaseLinkData(TypedDict):
    """Data required to show lease identifier with a link to that lease on reports."""

    id: int | None
    identifier: str | None


class LeaseRelatedModel(Protocol):
    lease: Lease


class LeaseWithContracts(Protocol):
    contracts: QuerySet[Contract]


def get_lease_type(lease):
    return lease.identifier.type.identifier


def get_lease_identifier_string(lease: Lease) -> str:
    return lease.get_identifier_string()


def get_lease_link_data(lease: Lease) -> LeaseLinkData:
    return {"id": lease.id, "identifier": lease.get_identifier_string()}


def get_lease_link_data_from_related_object(
    lease_related_object: LeaseRelatedModel,
) -> LeaseLinkData:
    try:
        return {
            "id": lease_related_object.lease.id,
            "identifier": lease_related_object.lease.get_identifier_string(),
        }
    except AttributeError:
        return {
            "id": None,
            "identifier": None,
        }


def get_identifier_string_from_lease_link_data(row: dict) -> str:
    try:
        return row["lease_identifier"]["identifier"] or "-"
    except KeyError:
        return "-"


def get_tenants(lease, include_future_tenants=False, report=None):
    today = datetime.date.today()

    contacts = set()

    for tenant in lease.tenants.all():
        all_tenantcontacts = tenant.tenantcontact_set.all()
        for tc in all_tenantcontacts:
            if report == "Lease statistics report" and len(all_tenantcontacts) == 1:
                include_future_tenants = True

            if tc.type != TenantContactType.TENANT:
                continue

            if (tc.end_date is None or tc.end_date >= today) and (
                include_future_tenants
                or tc.start_date is None
                or tc.start_date <= today
            ):
                contacts.add(tc.contact)

    return ", ".join([c.get_name() for c in contacts])


def get_address(lease):
    addresses = []

    for lease_area in lease.lease_areas.all():
        if lease_area.archived_at:
            continue

        for area_address in lease_area.addresses.all():
            if not area_address.is_primary:
                continue

            addresses.append(area_address.address)

    return " / ".join(addresses)


def get_latest_contract_number(lease: LeaseWithContracts):
    contracts: list[Contract] = []
    for contract in lease.contracts.all():
        if not contract.contract_number:
            continue

        # only accept contracts with lease contract type
        if not contract.type_id == 1:
            continue

        contracts.append(contract)

    latest_contract = max(
        contracts,
        key=lambda contract: (
            contract.signing_date
            if contract.signing_date is not None
            else datetime.date.min
        ),
        default=None,
    )

    if latest_contract is None or not latest_contract.contract_number:
        return ""

    return latest_contract.contract_number


def get_preparer(obj):
    if not obj.preparer:
        return
    return "{} {}".format(obj.preparer.last_name, obj.preparer.first_name)


def get_district(obj):
    if not obj.district:
        return
    return "{} {}".format(obj.district.identifier, obj.district.name)


def get_lease_area_identifier(obj):
    lease_area_identifiers = []

    for lease_area in obj.lease_areas.all():
        if lease_area.archived_at:
            continue

        lease_area_identifiers.extend([lease_area.identifier])

    return " / ".join(lease_area_identifiers)


def get_lessor(obj):
    if not obj.lessor:
        return
    return obj.lessor.name


def get_total_area(obj):
    total_area = 0
    for lease_area in obj.lease_areas.all():
        if lease_area.archived_at:
            continue

        total_area += lease_area.area

    return total_area


def get_supportive_housing(obj):
    if not obj.supportive_housing:
        return
    return obj.supportive_housing.name


def get_notice_period(obj):
    if not obj.notice_period:
        return
    return obj.notice_period.name


def get_form_of_management(obj):
    if not obj.management:
        return
    return obj.management.name


def get_form_of_regulation(obj):
    if not obj.regulation:
        return
    return obj.regulation.name


def get_re_lease(obj):
    for decision in obj.decisions.all():
        if decision.type_id == RE_LEASE_DECISION_TYPE_ID:
            return True
    return False


def get_option_to_purchase(obj):
    for decision in obj.decisions.all():
        for condition in decision.conditions.all():
            if condition.type_id == OPTION_TO_PURCHASE_CONDITION_TYPE_ID:
                return True

    return False
