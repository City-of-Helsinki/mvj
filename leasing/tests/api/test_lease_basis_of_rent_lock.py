import datetime
import json

import pytest

try:
    from zoneinfo import ZoneInfo  # type: ignore
except ImportError:
    from backports.zoneinfo import ZoneInfo

from django.contrib.auth.models import Permission
from django.core.serializers.json import DjangoJSONEncoder
from django.urls import reverse

from leasing.models import LeaseBasisOfRent


@pytest.mark.django_db
def test_lock_lease_basis_of_rent(
    django_db_setup, client, lease_test_data, user_factory, lease_basis_of_rent_factory
):
    user = user_factory(username="test_user")
    user.set_password("test_password")
    user.save()
    user.service_units.add(lease_test_data["lease"].service_unit)

    permission_codenames = [
        "view_lease",
        "change_lease",
        "add_leasebasisofrent",
        "change_lease_basis_of_rents",
        "change_leasebasisofrent",
        "change_leasebasisofrent_locked_at",
    ]
    for permission_codename in permission_codenames:
        permission = Permission.objects.get(codename=permission_codename)
        user.user_permissions.add(permission)

    client.login(username="test_user", password="test_password")

    lease = lease_test_data["lease"]

    lease_basis_of_rent = lease_basis_of_rent_factory(
        lease=lease, intended_use_id=1, area=12345, area_unit="m2", index_id=1
    )

    lock_time = datetime.datetime(
        year=2010,
        month=1,
        day=1,
        hour=1,
        minute=1,
        tzinfo=ZoneInfo("Europe/Helsinki"),
    )

    data = {
        "id": lease.id,
        "basis_of_rents": [{"id": lease_basis_of_rent.id, "locked_at": lock_time}],
    }

    url = reverse("lease-detail", kwargs={"pk": lease.id})

    response = client.patch(
        url,
        data=json.dumps(data, cls=DjangoJSONEncoder),
        content_type="application/json",
    )

    assert response.status_code == 200, "%s %s" % (response.status_code, response.data)

    lease_basis_of_rent = LeaseBasisOfRent.objects.get(pk=lease_basis_of_rent.id)

    assert lease_basis_of_rent.locked_at == lock_time


@pytest.mark.django_db
def test_cannot_change_locked_lease_basis_of_rent(
    django_db_setup, client, lease_test_data, user_factory, lease_basis_of_rent_factory
):
    user = user_factory(username="test_user")
    user.set_password("test_password")
    user.save()
    user.service_units.add(lease_test_data["lease"].service_unit)

    permission_codenames = [
        "view_lease",
        "change_lease",
        "add_leasebasisofrent",
        "change_lease_basis_of_rents",
        "change_leasebasisofrent",
        "change_leasebasisofrent_locked_at",
    ]
    for permission_codename in permission_codenames:
        permission = Permission.objects.get(codename=permission_codename)
        user.user_permissions.add(permission)

    client.login(username="test_user", password="test_password")

    lease = lease_test_data["lease"]

    lock_time = datetime.datetime(
        year=2010,
        month=1,
        day=1,
        hour=1,
        minute=1,
        tzinfo=ZoneInfo("Europe/Helsinki"),
    )

    lease_basis_of_rent = lease_basis_of_rent_factory(
        lease=lease,
        intended_use_id=1,
        area=12345,
        area_unit="m2",
        index_id=1,
        locked_at=lock_time,
    )

    data = {
        "id": lease.id,
        "basis_of_rents": [{"id": lease_basis_of_rent.id, "intended_use_id": 2}],
    }

    url = reverse("lease-detail", kwargs={"pk": lease.id})

    response = client.patch(
        url,
        data=json.dumps(data, cls=DjangoJSONEncoder),
        content_type="application/json",
    )

    assert response.status_code == 400, "%s %s" % (response.status_code, response.data)

    lease_basis_of_rent = LeaseBasisOfRent.objects.get(pk=lease_basis_of_rent.id)

    assert lease_basis_of_rent.intended_use_id == 1


@pytest.mark.django_db
def test_cannot_unclock_locked_lease_basis_of_rent(
    django_db_setup, client, lease_test_data, user_factory, lease_basis_of_rent_factory
):
    user = user_factory(username="test_user")
    user.set_password("test_password")
    user.save()
    user.service_units.add(lease_test_data["lease"].service_unit)

    permission_codenames = [
        "view_lease",
        "change_lease",
        "add_leasebasisofrent",
        "change_lease_basis_of_rents",
        "change_leasebasisofrent",
    ]
    for permission_codename in permission_codenames:
        permission = Permission.objects.get(codename=permission_codename)
        user.user_permissions.add(permission)

    client.login(username="test_user", password="test_password")

    lease = lease_test_data["lease"]

    lock_time = datetime.datetime(
        year=2010,
        month=1,
        day=1,
        hour=1,
        minute=1,
        tzinfo=ZoneInfo("Europe/Helsinki"),
    )

    lease_basis_of_rent = lease_basis_of_rent_factory(
        lease=lease,
        intended_use_id=1,
        area=12345,
        area_unit="m2",
        index_id=1,
        locked_at=lock_time,
    )

    data = {
        "id": lease.id,
        "basis_of_rents": [{"id": lease_basis_of_rent.id, "locked_at": None}],
    }

    url = reverse("lease-detail", kwargs={"pk": lease.id})

    response = client.patch(
        url,
        data=json.dumps(data, cls=DjangoJSONEncoder),
        content_type="application/json",
    )

    assert response.status_code == 200, "%s %s" % (response.status_code, response.data)

    lease_basis_of_rent = LeaseBasisOfRent.objects.get(pk=lease_basis_of_rent.id)

    assert lease_basis_of_rent.locked_at == lock_time


@pytest.mark.django_db
def test_can_unclock_locked_lease_basis_of_rent(
    django_db_setup, client, lease_test_data, user_factory, lease_basis_of_rent_factory
):
    user = user_factory(username="test_user")
    user.set_password("test_password")
    user.save()
    user.service_units.add(lease_test_data["lease"].service_unit)

    permission_codenames = [
        "view_lease",
        "change_lease",
        "add_leasebasisofrent",
        "change_lease_basis_of_rents",
        "change_leasebasisofrent",
        "change_leasebasisofrent_locked_at",
    ]
    for permission_codename in permission_codenames:
        permission = Permission.objects.get(codename=permission_codename)
        user.user_permissions.add(permission)

    client.login(username="test_user", password="test_password")

    lease = lease_test_data["lease"]

    lock_time = datetime.datetime(
        year=2010,
        month=1,
        day=1,
        hour=1,
        minute=1,
        tzinfo=ZoneInfo("Europe/Helsinki"),
    )

    lease_basis_of_rent = lease_basis_of_rent_factory(
        lease=lease,
        intended_use_id=1,
        area=12345,
        area_unit="m2",
        index_id=1,
        locked_at=lock_time,
    )

    data = {
        "id": lease.id,
        "basis_of_rents": [{"id": lease_basis_of_rent.id, "locked_at": None}],
    }

    url = reverse("lease-detail", kwargs={"pk": lease.id})

    response = client.patch(
        url,
        data=json.dumps(data, cls=DjangoJSONEncoder),
        content_type="application/json",
    )

    assert response.status_code == 200, "%s %s" % (response.status_code, response.data)

    lease_basis_of_rent = LeaseBasisOfRent.objects.get(pk=lease_basis_of_rent.id)

    assert lease_basis_of_rent.locked_at is None


@pytest.mark.django_db
def test_cannot_remove_locked_lease_basis_of_rent(
    django_db_setup, client, lease_test_data, user_factory, lease_basis_of_rent_factory
):
    user = user_factory(username="test_user")
    user.set_password("test_password")
    user.save()
    user.service_units.add(lease_test_data["lease"].service_unit)

    permission_codenames = [
        "view_lease",
        "change_lease",
        "add_leasebasisofrent",
        "delete_leasebasisofrent",
        "change_lease_basis_of_rents",
        "change_leasebasisofrent",
        "change_leasebasisofrent_locked_at",
    ]
    for permission_codename in permission_codenames:
        permission = Permission.objects.get(codename=permission_codename)
        user.user_permissions.add(permission)

    client.login(username="test_user", password="test_password")

    lease = lease_test_data["lease"]

    lock_time = datetime.datetime(
        year=2010,
        month=1,
        day=1,
        hour=1,
        minute=1,
        tzinfo=ZoneInfo("Europe/Helsinki"),
    )

    lease_basis_of_rent_factory(
        lease=lease,
        intended_use_id=1,
        area=12345,
        area_unit="m2",
        index_id=1,
        locked_at=lock_time,
    )

    data = {"id": lease.id, "basis_of_rents": []}

    url = reverse("lease-detail", kwargs={"pk": lease.id})

    response = client.patch(
        url,
        data=json.dumps(data, cls=DjangoJSONEncoder),
        content_type="application/json",
    )

    assert response.status_code == 200, "%s %s" % (response.status_code, response.data)

    assert lease.basis_of_rents.count() == 1
