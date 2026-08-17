import datetime
from unittest.mock import MagicMock

import pytest
from django.utils import timezone
from rest_framework import serializers

from leasing.enums import TenantContactType
from leasing.models.lease import Lease
from leasing.serializers.lease import (
    LeaseCreateSerializer,
    LeasesForContactSerializer,
    LeaseUpdateSerializer,
)
from leasing.viewsets.lease_additional_views import LeasesForContactViewSet


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


# ---------------------------------------------------------------------------
# LeasesForContactSerializer
# ---------------------------------------------------------------------------


def _make_serializer(lease, contact_id):
    request = MagicMock()
    request.query_params = {"contact": str(contact_id)}
    viewset = LeasesForContactViewSet()
    viewset.request = request
    annotated_lease = viewset.get_queryset().get(pk=lease.pk)
    return LeasesForContactSerializer(annotated_lease, context={"request": request})


@pytest.mark.django_db
def test_is_active_future_start_date(lease_test_data):
    lease = lease_test_data["lease"]
    contact = lease_test_data["tenantcontacts"][0].contact
    lease.start_date = timezone.now().date() + datetime.timedelta(days=1)
    lease.end_date = None
    lease.save()

    serializer = _make_serializer(lease, contact.id)
    assert serializer.data["is_active"] is False


@pytest.mark.django_db
def test_is_active_no_end_date(lease_test_data):
    lease = lease_test_data["lease"]
    contact = lease_test_data["tenantcontacts"][0].contact
    lease.start_date = datetime.date(2000, 1, 1)
    lease.end_date = None
    lease.save()

    serializer = _make_serializer(lease, contact.id)
    assert serializer.data["is_active"] is True


@pytest.mark.django_db
def test_is_active_end_date_today(lease_test_data):
    lease = lease_test_data["lease"]
    contact = lease_test_data["tenantcontacts"][0].contact
    lease.start_date = datetime.date(2000, 1, 1)
    lease.end_date = timezone.now().date()
    lease.save()

    serializer = _make_serializer(lease, contact.id)
    assert serializer.data["is_active"] is True


@pytest.mark.django_db
def test_is_active_end_date_yesterday(lease_test_data):
    lease = lease_test_data["lease"]
    contact = lease_test_data["tenantcontacts"][0].contact
    lease.start_date = datetime.date(2000, 1, 1)
    lease.end_date = timezone.now().date() - datetime.timedelta(days=1)
    lease.save()

    serializer = _make_serializer(lease, contact.id)
    assert serializer.data["is_active"] is False


@pytest.mark.django_db
def test_contact_roles_returns_correct_types(
    lease_test_data,
):
    lease = lease_test_data["lease"]
    tenantcontacts = lease_test_data["tenantcontacts"]
    tc = tenantcontacts[0]  # type is TenantContactType.TENANT
    contact = tc.contact

    serializer = _make_serializer(lease, contact.id)
    roles = serializer.data["contact_roles"]
    assert TenantContactType.TENANT.value in roles


@pytest.mark.django_db
def test_contact_roles_deduplicates(
    lease_test_data,
    tenant_contact_factory,
):
    """Two TENANT tenantcontacts for the same contact should yield one role entry."""
    lease = lease_test_data["lease"]
    tc = lease_test_data["tenantcontacts"][0]
    contact = tc.contact

    # Add a second TENANT tenantcontact for the same contact on the same tenant
    tenant_contact_factory(
        type=TenantContactType.TENANT,
        tenant=tc.tenant,
        contact=contact,
        start_date=datetime.date(2021, 1, 1),
    )

    serializer = _make_serializer(lease, contact.id)
    roles = serializer.data["contact_roles"]
    assert roles.count(TenantContactType.TENANT.value) == 1


@pytest.mark.django_db
def test_contact_roles_excludes_soft_deleted_tenantcontacts(
    lease_test_data,
    tenant_contact_factory,
):
    """Soft-deleted tenantcontacts must not contribute roles."""
    lease = lease_test_data["lease"]
    tc = lease_test_data["tenantcontacts"][0]
    contact = tc.contact

    tenant_contact_factory(
        type=TenantContactType.CONTACT,
        tenant=tc.tenant,
        contact=contact,
        start_date=datetime.date(2021, 1, 1),
    )
    tc.delete()

    serializer = _make_serializer(lease, contact.id)
    roles = serializer.data["contact_roles"]
    assert TenantContactType.TENANT.value not in roles


@pytest.mark.django_db
def test_contact_roles_ignores_other_contacts(
    lease_test_data,
):
    """Roles from a different contact's tenantcontacts should not appear."""
    lease = lease_test_data["lease"]
    # tenantcontacts[1] belongs to contacts[2]
    other_tc = lease_test_data["tenantcontacts"][1]  # noqa: F841
    our_tc = lease_test_data["tenantcontacts"][2]  # CONTACT type
    contact = our_tc.contact

    serializer = _make_serializer(lease, contact.id)
    roles = serializer.data["contact_roles"]
    assert TenantContactType.CONTACT.value in roles
    # Should not include roles from the other contact
    assert len(roles) == 1


@pytest.mark.django_db
def test_contact_role_active_when_currently_active(
    lease_test_data,
):
    """contact_role_active is True when at least one tenantcontact is active today."""
    lease = lease_test_data["lease"]
    tc = lease_test_data["tenantcontacts"][0]
    contact = tc.contact

    # start_date is in the past and end_date is None → active
    tc.start_date = datetime.date(2000, 1, 1)
    tc.end_date = None
    tc.save()

    serializer = _make_serializer(lease, contact.id)
    assert serializer.data["contact_role_active"] is True


@pytest.mark.django_db
def test_contact_role_active_false_when_expired(
    lease_test_data,
):
    """contact_role_active is False when the tenantcontact's end_date is in the past."""
    lease = lease_test_data["lease"]
    tc = lease_test_data["tenantcontacts"][0]
    contact = tc.contact

    tc.start_date = datetime.date(2000, 1, 1)
    tc.end_date = datetime.date(2001, 1, 1)
    tc.save()

    serializer = _make_serializer(lease, contact.id)
    assert serializer.data["contact_role_active"] is False


@pytest.mark.django_db
def test_contact_role_active_false_when_future_start(
    lease_test_data,
):
    """contact_role_active is False when the tenantcontact hasn't started yet."""
    lease = lease_test_data["lease"]
    tc = lease_test_data["tenantcontacts"][0]
    contact = tc.contact

    tc.start_date = timezone.now().date() + datetime.timedelta(days=30)
    tc.end_date = None
    tc.save()

    serializer = _make_serializer(lease, contact.id)
    assert serializer.data["contact_role_active"] is False
