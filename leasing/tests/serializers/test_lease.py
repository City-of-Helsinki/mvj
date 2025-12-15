import datetime

import pytest
from rest_framework import serializers

from leasing.models.lease import Lease
from leasing.serializers.lease import LeaseCreateSerializer, LeaseUpdateSerializer


@pytest.fixture
def lease_with_mandatory_received_date(
    service_unit_factory,
    lease_factory,
) -> Lease:
    """
    Create lease with a service unit, which has is_application_received_at_mandatory enabled
    """
    service_unit_with_mandatory_received_at = service_unit_factory(
        name="Service unit with mandatory received date",
        is_application_received_at_mandatory=True,
    )
    return lease_factory(
        service_unit=service_unit_with_mandatory_received_at,
    )


@pytest.mark.django_db
def test_validate_mandatory_application_received_at_update(
    lease_with_mandatory_received_date,
):
    """
    LeaseUpdateSerializer should validate application_metadata
    when application_received_at is set and service unit requires it.
    """
    application_metadata = {"application_received_at": datetime.date(2025, 12, 5)}
    empty_application_metadata = {"application_received_at": None}

    serializer = LeaseUpdateSerializer()
    serializer.instance = lease_with_mandatory_received_date

    assert serializer.validate_application_metadata(application_metadata)
    with pytest.raises(serializers.ValidationError):
        serializer.validate_application_metadata(empty_application_metadata)


@pytest.mark.django_db
def test_validate_application_received_at_update(
    lease_test_data,
):
    """
    LeaseUpdateSerializer should validate application_metadata
    regardless if application_received_at is set or not when service unit doesn't require it.
    """
    application_metadata = {"application_received_at": datetime.date(2025, 12, 5)}
    empty_application_metadata = {"application_received_at": None}

    serializer = LeaseUpdateSerializer()
    serializer.instance = lease_test_data.get("lease")

    assert serializer.validate_application_metadata(application_metadata)
    assert serializer.validate_application_metadata(empty_application_metadata)


@pytest.mark.django_db
def test_validate_mandatory_application_received_at_create(
    lease_with_mandatory_received_date,
):
    """
    LeaseCreateSerializer should validate application_metadata
    when application_received_at is set and service unit requires it.
    """
    lease_data = {
        "service_unit": lease_with_mandatory_received_date.service_unit,
        "application_metadata": {"application_received_at": datetime.date(2025, 12, 5)},
    }
    serializer = LeaseCreateSerializer()

    assert serializer.validate(lease_data)

    lease_data["application_metadata"] = None
    with pytest.raises(serializers.ValidationError):
        serializer.validate(lease_data)


@pytest.mark.django_db
def test_validate_application_received_at_create(
    lease_test_data,
):
    """
    LeaseCreateSerializer should validate application_metadata
    regardless if application_received_at is set or not when service unit doesn't require it.
    """
    lease_data = {
        "service_unit": lease_test_data.get("lease").service_unit,
        "application_metadata": {"application_received_at": datetime.date(2025, 12, 5)},
    }
    serializer = LeaseCreateSerializer()

    assert serializer.validate(lease_data)

    lease_data["application_metadata"] = None
    assert serializer.validate(lease_data)
