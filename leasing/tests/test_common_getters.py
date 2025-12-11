# test common_getters related to lease_link data

import pytest

from leasing.report.lease.common_getters import (
    form_lease_url,
    get_identifier_string_from_lease_link_data,
    get_lease_link_data,
    get_lease_link_data_from_related_object,
)


@pytest.mark.django_db
def test_get_lease_link_data_from_related_object(contract_factory, lease_factory):
    lease = lease_factory()
    contract = contract_factory(lease=lease, type_id=1)

    lease_link_data = get_lease_link_data_from_related_object(contract)
    lease_url = form_lease_url(lease.id)

    assert lease_link_data["url"] == lease_url
    assert lease_link_data["name"] == lease.get_identifier_string()

    contract_without_lease = contract_factory(lease=None, type_id=1)
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
