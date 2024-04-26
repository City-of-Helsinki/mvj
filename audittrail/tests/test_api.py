import pytest
from django.contrib.auth.models import Permission
from django.urls import reverse
from rest_framework.test import APIClient

from leasing.enums import ContactType


@pytest.mark.django_db
def test_audittrail_get_permissions(lease_factory, contact_factory, user_factory):
    contact = contact_factory(
        first_name="Jane",
        last_name="Doe",
        type=ContactType.PERSON,
        national_identification_number="011213-1234",
    )
    lease = lease_factory()

    user = user_factory()
    permissions = Permission.objects.filter(codename__in=["view_lease"])
    user.user_permissions.add(*permissions)
    client = APIClient()
    client.force_authenticate(user=user)
    response = client.get(reverse("audittrail"), {"type": "lease", "id": lease.id})
    assert response.status_code == 200
    (logentry, *_,) = response.json().get("results")
    assert (
        logentry.get("object_id") == lease.id
        and logentry.get("content_type") == "lease"
        and logentry.get("action") == "create"
    ), "Lease creation should be in auditlog response."

    lease.lessor = contact
    lease.save()

    response = client.get(reverse("audittrail"), {"type": "lease", "id": lease.id})
    assert response.status_code == 200
    data = response.json().get("results")
    assert not any(
        x.get("content_type") == "contact" for x in data
    ), "Contact object should not be in as user has no view permission."

    permissions = Permission.objects.filter(codename__in=["view_lease", "view_contact"])
    # Django caches permissions for users, creating new users avoids this cache issue
    user = user_factory()
    user.user_permissions.add(*permissions)
    client.force_authenticate(user=user)
    response = client.get(reverse("audittrail"), {"type": "lease", "id": lease.id})
    assert response.status_code == 200
    data = response.json().get("results")
    assert any(
        x.get("content_type") == "contact" for x in data
    ), "Contact object should be in response as view permission was added."


@pytest.mark.django_db
def test_audittrail_get_types(
    user_factory, lease_factory, contact_factory, area_search_factory
):
    user = user_factory()
    lease = lease_factory()
    contact = contact_factory(
        first_name="Jane",
        last_name="Doe",
        type=ContactType.PERSON,
        national_identification_number="011213-1234",
    )
    areasearch = area_search_factory(
        description_area="Test"
    )
    objs = [lease, contact, areasearch]
    client = APIClient()
    client.force_authenticate(user=user)
    for model_name in ["comment", "plotsearch"]:
        response = client.get(reverse("audittrail"), {"type": model_name, "id": 1})
        assert (
            response.status_code == 400
        ), f"{model_name} should not be a valid option for type"

    # Create new user to avoid permission cache issues
    user = user_factory()
    permissions = Permission.objects.filter(
        codename__in=["view_lease", "view_contact", "view_areasearch"]
    )
    user.user_permissions.add(*permissions)
    client.force_authenticate(user=user)
    for obj in objs:
        model_name = obj._meta.model_name
        response = client.get(reverse("audittrail"), {"type": model_name, "id": obj.id})
        assert (
            response.status_code == 200
        ), f"{model_name} should be a valid option for model_name"
