# test common_getters related to lease_link data

import pytest

from leasing.report.lease.common_getters import (
    get_identifier_string_from_lease_link_data,
    get_lease_link_data,
    get_lease_link_data_from_related_object,
)


@pytest.mark.django_db
def test_get_lease_link_data_from_related_object(contract_factory, lease_factory):
    lease = lease_factory()
    contract = contract_factory(lease=lease, type_id=1)

    lease_link_data = get_lease_link_data_from_related_object(contract)

    assert lease_link_data["id"] == lease.id
    assert lease_link_data["identifier"] == lease.get_identifier_string()

    contract_without_lease = contract_factory(lease=None, type_id=1)
    lease_link_data = get_lease_link_data_from_related_object(contract_without_lease)
    assert lease_link_data["id"] is None
    assert lease_link_data["identifier"] is None


# test get_identifier_string_from_lease_link_data
@pytest.mark.django_db
def test_get_identifier_string_from_lease_link_data(lease_factory):
    lease = lease_factory()
    lease_link_data = get_lease_link_data(lease)

    row = {"lease_identifier": lease_link_data}

    assert (
        get_identifier_string_from_lease_link_data(row) == lease.get_identifier_string()
    )

    row = {"lease_identifier": {"id": None, "identifier": None}}
    assert get_identifier_string_from_lease_link_data(row) == "-"
