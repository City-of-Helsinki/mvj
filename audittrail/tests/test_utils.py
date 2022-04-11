import pytest
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

from audittrail.utils import recursive_get_related
from audittrail.viewsets import TYPE_MAP
from leasing.enums import ContactType
from leasing.models import ServiceUnit


@pytest.mark.django_db
def test_recursive_get_related(lease_factory, contact_factory, user_factory):
    (service_unit, created) = ServiceUnit.objects.get_or_create(id=1)
    contact = contact_factory(
        first_name="Jane",
        last_name="Doe",
        type=ContactType.PERSON,
        national_identification_number="011213-1234",
        service_unit=service_unit,
    )
    lease = lease_factory(service_unit=service_unit)

    user = user_factory()
    user.service_units.add(service_unit)
    exclude_apps = TYPE_MAP["lease"].get("exclude_apps", None)
    permissions = Permission.objects.filter(codename__in=["view_lease"])
    user.user_permissions.add(*permissions)
    collected_items = recursive_get_related(lease, user=user, exclude_apps=exclude_apps)
    contact_content_type = ContentType.objects.get_for_model(contact)
    assert (
        contact_content_type not in collected_items
    ), "Contact should not be in as it does not exist yet."

    lease.lessor = contact
    lease.save()
    collected_items = recursive_get_related(lease, user=user, exclude_apps=exclude_apps)
    assert (
        contact_content_type not in collected_items
    ), "Contact should not be visible as user does not have permissions to see them."

    permissions = Permission.objects.filter(codename__in=["view_lease", "view_contact"])
    # Django caches permissions for users, creating new users avoids this cache issue
    user = user_factory()
    user.user_permissions.add(*permissions)
    collected_items_with_contact = recursive_get_related(
        lease, user=user, exclude_apps=exclude_apps
    )
    assert (
        contact_content_type in collected_items_with_contact
    ), "Contact should be visible as user has permissions to see them."
