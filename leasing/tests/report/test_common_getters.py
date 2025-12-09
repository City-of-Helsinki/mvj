# test common_getters related to lease_link data

import datetime

import pytest

from leasing.report.lease.common_getters import (
    LEASING_CONTRACT_TYPE_NAME,
    _get_latest_contract,
    get_identifier_string_from_lease_link_data,
    get_latest_contract_number,
    get_latest_contract_signing_date,
    get_lease_link_data,
    get_lease_link_data_from_related_object,
)


@pytest.fixture
def non_leasing_contract_type(contract_type_factory):
    return contract_type_factory(name="Non-leasing contract")


@pytest.fixture
def leasing_contract_type(contract_type_factory):
    return contract_type_factory(name=LEASING_CONTRACT_TYPE_NAME)


@pytest.mark.django_db
def test_get_lease_link_data_from_related_object(
    contract_factory, lease_factory, leasing_contract_type
):
    lease = lease_factory()
    contract = contract_factory(lease=lease, type=leasing_contract_type)

    lease_link_data = get_lease_link_data_from_related_object(contract)

    assert lease_link_data["url"] == lease.id
    assert lease_link_data["name"] == lease.get_identifier_string()

    contract_without_lease = contract_factory(lease=None, type=leasing_contract_type)
    lease_link_data = get_lease_link_data_from_related_object(contract_without_lease)
    assert lease_link_data["url"] is None
    assert lease_link_data["name"] is None


@pytest.mark.django_db
def test_get_identifier_string_from_lease_link_data(lease_factory):
    lease = lease_factory()
    lease_link_data = get_lease_link_data(lease)

    row = {"lease_identifier": lease_link_data}

    assert (
        get_identifier_string_from_lease_link_data(row) == lease.get_identifier_string()
    )

    non_lease_link_data_rows = [
        None,
        "123",
        {"lease_identifier": {}},
        {"lease_identifier": None},
        {"lease_identifier": {"url": None, "name": None}},
        {"lease_identifier": {"name": {}}},
        {"lease_identifier": {"name": ""}},
    ]
    for row in non_lease_link_data_rows:
        assert get_identifier_string_from_lease_link_data(row) == "-"

    row = {"lease_identifier": lease.get_identifier_string()}
    assert (
        get_identifier_string_from_lease_link_data(row) == lease.get_identifier_string()
    )


@pytest.mark.django_db
def test_get_latest_contract_returns_none_when_no_contracts(lease_factory):
    lease = lease_factory()
    result = _get_latest_contract(lease)
    assert result is None


@pytest.mark.django_db
def test_get_latest_contract_returns_none_when_no_leasing_contracts(
    lease_factory, contract_factory, non_leasing_contract_type
):
    lease = lease_factory()
    # Create contracts with different type than leasing contract
    contract_factory(lease=lease, type=non_leasing_contract_type, contract_number="2")
    contract_factory(lease=lease, type=non_leasing_contract_type, contract_number="3")
    result = _get_latest_contract(lease)
    assert result is None


@pytest.mark.django_db
def test_get_latest_contract_returns_none_when_contract_has_no_number(
    lease_factory, contract_factory, leasing_contract_type
):
    lease = lease_factory()
    contract_factory(lease=lease, type=leasing_contract_type, contract_number=None)
    result = _get_latest_contract(lease)
    assert result is None


@pytest.mark.django_db
def test_get_latest_contract_returns_single_valid_contract(
    lease_factory, contract_factory, leasing_contract_type
):
    lease = lease_factory()
    contract = contract_factory(
        lease=lease,
        type=leasing_contract_type,
        contract_number="1",
        signing_date=datetime.date(2025, 1, 1),
    )
    result = _get_latest_contract(lease)
    assert result == contract


@pytest.mark.django_db
def test_get_latest_contract_returns_contract_with_latest_signing_date(
    lease_factory, contract_factory, leasing_contract_type
):
    lease = lease_factory()
    older_contract = contract_factory(  # noqa: F841 (unused variable by purpose)
        lease=lease,
        type=leasing_contract_type,
        contract_number="1",
        signing_date=datetime.date(2020, 1, 1),
    )
    latest_contract = contract_factory(
        lease=lease,
        type=leasing_contract_type,
        contract_number="2",
        signing_date=datetime.date(2025, 1, 1),
    )
    middle_contract = contract_factory(  # noqa: F841 (unused variable by purpose)
        lease=lease,
        type=leasing_contract_type,
        contract_number="3",
        signing_date=datetime.date(2023, 1, 1),
    )
    result = _get_latest_contract(lease)
    assert result == latest_contract


@pytest.mark.django_db
def test_get_latest_contract_handles_none_signing_dates(
    lease_factory, contract_factory, leasing_contract_type
):
    lease = lease_factory()
    contract_without_date = contract_factory(  # noqa: F841 (unused variable by purpose)
        lease=lease,
        type=leasing_contract_type,
        contract_number="1",
        signing_date=None,
    )
    contract_with_date = contract_factory(
        lease=lease,
        type=leasing_contract_type,
        contract_number="2",
        signing_date=datetime.date(2025, 1, 1),
    )
    result = _get_latest_contract(lease)
    # Contract with date should be preferred over None
    assert result == contract_with_date


@pytest.mark.django_db
def test_get_latest_contract_ignores_wrong_contract_types(
    lease_factory, contract_factory, leasing_contract_type, non_leasing_contract_type
):
    lease = lease_factory()
    contract_with_wrong_type = (  # noqa: F841 (unused variable by purpose)
        contract_factory(
            lease=lease,
            type=non_leasing_contract_type,
            contract_number="1",
            signing_date=datetime.date(2025, 1, 1),
        )
    )
    leasing_contract = contract_factory(
        lease=lease,
        type=leasing_contract_type,
        contract_number="2",
        signing_date=datetime.date(2022, 1, 1),
    )
    result = _get_latest_contract(lease)
    assert result == leasing_contract


@pytest.mark.django_db
def test_get_latest_contract_number_returns_empty_string_when_no_contracts(
    lease_factory,
):
    lease = lease_factory()
    result = get_latest_contract_number(lease)
    assert result == ""


@pytest.mark.django_db
def test_get_latest_contract_number_returns_empty_string_when_no_valid_contracts(
    lease_factory, contract_factory, non_leasing_contract_type
):
    lease = lease_factory()
    contract_factory(lease=lease, type=non_leasing_contract_type, contract_number="1")
    result = get_latest_contract_number(lease)
    assert result == ""


@pytest.mark.django_db
def test_get_latest_contract_number_returns_contract_number(
    lease_factory, contract_factory, leasing_contract_type
):
    lease = lease_factory()
    contract_factory(
        lease=lease,
        type=leasing_contract_type,
        contract_number="1",
        signing_date=datetime.date(2025, 1, 1),
    )
    result = get_latest_contract_number(lease)
    assert result == "1"


@pytest.mark.django_db
def test_get_latest_contract_number_returns_latest_contract_number(
    lease_factory, contract_factory, leasing_contract_type
):
    lease = lease_factory()
    contract_factory(
        lease=lease,
        type=leasing_contract_type,
        contract_number="1",
        signing_date=datetime.date(2022, 1, 1),
    )
    contract_factory(
        lease=lease,
        type=leasing_contract_type,
        contract_number="2",
        signing_date=datetime.date(2025, 1, 1),
    )
    result = get_latest_contract_number(lease)
    assert result == "2"


@pytest.mark.django_db
def test_get_latest_contract_number_returns_empty_when_contract_number_is_none(
    lease_factory, contract_factory, leasing_contract_type
):
    lease = lease_factory()
    contract_factory(
        lease=lease,
        type=leasing_contract_type,
        contract_number=None,
        signing_date=datetime.date(2025, 1, 1),
    )
    result = get_latest_contract_number(lease)
    assert result == ""


@pytest.mark.django_db
def test_get_latest_contract_signing_date_returns_empty_string_when_no_contracts(
    lease_factory,
):
    lease = lease_factory()
    result = get_latest_contract_signing_date(lease)
    assert result == ""


@pytest.mark.django_db
def test_get_latest_contract_signing_date_returns_empty_string_when_no_valid_contracts(
    lease_factory, contract_factory, non_leasing_contract_type
):
    lease = lease_factory()
    contract_factory(
        lease=lease,
        type=non_leasing_contract_type,
        contract_number="1",
        signing_date=datetime.date(2025, 1, 1),
    )
    result = get_latest_contract_signing_date(lease)
    assert result == ""


@pytest.mark.django_db
def test_get_latest_contract_signing_date_returns_signing_date(
    lease_factory, contract_factory, leasing_contract_type
):
    lease = lease_factory()
    expected_date = datetime.date(2025, 1, 1)
    contract_factory(
        lease=lease,
        type=leasing_contract_type,
        contract_number="1",
        signing_date=expected_date,
    )
    result = get_latest_contract_signing_date(lease)
    assert result == expected_date


@pytest.mark.django_db
def test_get_latest_contract_signing_date_returns_latest_signing_date(
    lease_factory, contract_factory, leasing_contract_type
):
    lease = lease_factory()
    older_date = datetime.date(2010, 1, 1)
    latest_date = datetime.date(2020, 1, 1)

    contract_factory(
        lease=lease,
        type=leasing_contract_type,
        contract_number="1",
        signing_date=older_date,
    )
    contract_factory(
        lease=lease,
        type=leasing_contract_type,
        contract_number="2",
        signing_date=latest_date,
    )
    result = get_latest_contract_signing_date(lease)
    assert result == latest_date


@pytest.mark.django_db
def test_get_latest_contract_signing_date_returns_empty_when_signing_date_is_none(
    lease_factory, contract_factory, leasing_contract_type
):
    lease = lease_factory()
    contract_factory(
        lease=lease,
        type=leasing_contract_type,
        contract_number="1",
        signing_date=None,
    )
    result = get_latest_contract_signing_date(lease)
    assert result == ""
