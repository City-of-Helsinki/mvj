import pytest
from django.contrib.auth.models import Permission
from django.urls import reverse

from leasing.models import ServiceUnit


@pytest.mark.django_db
def test_user_can_delete_empty_lease(
    django_db_setup, client, lease_factory, user_factory
):
    # Service unit from the fixtures
    service_unit = ServiceUnit.objects.get(pk=1)

    user = user_factory(username="test_user")
    user.service_units.add(service_unit)

    lease = lease_factory(
        type_id=1,
        municipality_id=1,
        district_id=1,
        notice_period_id=1,
        service_unit=service_unit,
        preparer=user,
    )

    permission_names = [
        "delete_lease",
    ]

    for permission_name in permission_names:
        user.user_permissions.add(Permission.objects.get(codename=permission_name))

    client.force_login(user)
    url = reverse("v1:lease-detail", kwargs={"pk": lease.id})
    response = client.delete(url)

    assert response.status_code == 204, "%s %s" % (response.status_code, response.data)

    lease.refresh_from_db()

    assert lease.deleted is not None


@pytest.mark.django_db
def test_user_can_delete_non_empty_lease_with_permission(
    django_db_setup, client, lease_factory, user_factory
):
    # Service unit from the fixtures
    service_unit = ServiceUnit.objects.get(pk=1)

    user = user_factory(username="test_user")
    user.service_units.add(service_unit)

    lease = lease_factory(
        type_id=1,
        municipality_id=1,
        district_id=1,
        notice_period_id=1,
        service_unit=service_unit,
    )

    permission_names = [
        "delete_lease",
        "delete_nonempty_lease",
    ]

    for permission_name in permission_names:
        user.user_permissions.add(Permission.objects.get(codename=permission_name))

    client.force_login(user)
    url = reverse("v1:lease-detail", kwargs={"pk": lease.id})
    response = client.delete(url)

    assert response.status_code == 204, "%s %s" % (response.status_code, response.data)

    lease.refresh_from_db()

    assert lease.deleted is not None


@pytest.mark.django_db
def test_user_cannot_delete_empty_lease_from_another_service_unit(
    django_db_setup, client, lease_factory, user_factory, service_unit_factory
):
    service_unit = service_unit_factory()
    service_unit2 = service_unit_factory()

    user = user_factory(username="test_user")
    user.service_units.add(service_unit)

    lease = lease_factory(
        type_id=1,
        municipality_id=1,
        district_id=1,
        notice_period_id=1,
        service_unit=service_unit2,
    )

    permission_names = [
        "delete_lease",
        "delete_nonempty_lease",
    ]

    for permission_name in permission_names:
        user.user_permissions.add(Permission.objects.get(codename=permission_name))

    client.force_login(user)
    url = reverse("v1:lease-detail", kwargs={"pk": lease.id})
    response = client.delete(url)

    assert response.status_code == 403, "%s %s" % (response.status_code, response.data)

    lease.refresh_from_db()

    assert lease.deleted is None
