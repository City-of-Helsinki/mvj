import pytest

from leasing.enums import LeaseState, TenantContactType


@pytest.mark.django_db
def test_lease_search_form_no_fields_required():
    from leasing.forms import LeaseSearchForm

    form = LeaseSearchForm({})
    assert form.is_valid()


@pytest.mark.parametrize(
    "business_id, expected",
    [
        (None, True),
        ("", True),
        ("0", False),
        (123, False),
        ("something", True),
        ("1234567-8", True),
        ("123456", False),
        ("1234567-89", False),
    ],
)
@pytest.mark.django_db
def test_lease_search_form_business_id(business_id, expected):
    from leasing.forms import LeaseSearchForm

    form = LeaseSearchForm({"business_id": business_id})

    assert expected == form.is_valid()


@pytest.mark.parametrize(
    "tenantcontact_type, expected",
    [
        (None, True),
        ("", True),
        ("0", False),
        (123, False),
        ("something", False),
        (TenantContactType.TENANT.value, True),
        (TenantContactType.BILLING.value, True),
        (TenantContactType.CONTACT.value, True),
        (
            ",".join([TenantContactType.TENANT.value, TenantContactType.CONTACT.value]),
            True,
        ),
        (
            " , ".join(
                [TenantContactType.TENANT.value, TenantContactType.CONTACT.value]
            ),
            True,
        ),
        (
            ";".join([TenantContactType.TENANT.value, TenantContactType.CONTACT.value]),
            False,
        ),
        (
            " ".join([TenantContactType.TENANT.value, TenantContactType.CONTACT.value]),
            False,
        ),
    ],
)
@pytest.mark.django_db
def test_lease_search_form_tenantcontact_type_choices(tenantcontact_type, expected):
    from leasing.forms import LeaseSearchForm

    form = LeaseSearchForm({"tenantcontact_type": tenantcontact_type})

    assert expected == form.is_valid()


@pytest.mark.parametrize(
    "lease_type, expected",
    [(None, True), ("", True), ("0", False), (123, False), (1, True), (2, True)],
)
@pytest.mark.django_db
def test_lease_search_form_lease_type_choices(lease_type, expected):
    from leasing.forms import LeaseSearchForm

    form = LeaseSearchForm({"lease_type": lease_type})

    assert expected == form.is_valid()


@pytest.mark.parametrize(
    "lease_state, expected",
    [
        (None, True),
        ("", True),
        ("0", False),
        (123, False),
        ("something", False),
        (LeaseState.LEASE.value, True),
        (LeaseState.RESERVATION.value, True),
        (",".join([LeaseState.LEASE.value, LeaseState.RESERVATION.value]), True),
        (" , ".join([LeaseState.LEASE.value, LeaseState.RESERVATION.value]), True),
        (";".join([LeaseState.LEASE.value, LeaseState.RESERVATION.value]), False),
        (" ".join([LeaseState.LEASE.value, LeaseState.RESERVATION.value]), False),
    ],
)
@pytest.mark.django_db
def test_lease_search_form_lease_state_choices(lease_state, expected):
    from leasing.forms import LeaseSearchForm

    form = LeaseSearchForm({"lease_state": lease_state})

    assert expected == form.is_valid()
