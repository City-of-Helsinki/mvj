import datetime
import functools

from leasing.enums import TenantContactType

RE_LEASE_DECISION_TYPE_ID = 29  # Vuokraus (sopimuksen uusiminen/jatkam.)

OPTION_TO_PURCHASE_CONDITION_TYPE_ID = 24  # 24 = Osto-optioehto


def get_lease_type(lease):
    return lease.identifier.type.identifier


def get_lease_id(lease):
    return lease.get_identifier_string()


def get_tenants(lease, include_future_tenants=False):
    today = datetime.date.today()

    contacts = set()

    for tenant in lease.tenants.all():
        for tc in tenant.tenantcontact_set.all():
            if tc.type != TenantContactType.TENANT:
                continue

            if (tc.end_date is None or tc.end_date >= today) and (
                include_future_tenants
                or (tc.start_date is None or tc.start_date <= today)
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


def get_contract_number(obj):
    contracts = []
    for contract in obj.contracts.all():
        if not contract.contract_number:
            continue

        # only accept contracts with lease contract type
        if not contract.type_id == 1:
            continue

        contracts.append(contract)

    if len(contracts) == 0:
        return ""
    else:
        latest_contract = functools.reduce(
            lambda a, b: (a if a.signing_date > b.signing_date else b),
            contracts,
        )

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
