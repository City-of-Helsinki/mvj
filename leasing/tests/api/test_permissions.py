import pytest
from django.contrib.auth.models import Permission
from django.urls import reverse


@pytest.mark.django_db
def test_anonymous_user_cannot_view_lease(django_db_setup, client, lease_test_data):
    url = reverse("v1:lease-detail", kwargs={"pk": lease_test_data["lease"].id})

    response = client.get(url)

    assert response.status_code == 401, "%s %s" % (response.status_code, response.data)
    assert response.data["detail"].code == "not_authenticated"


@pytest.mark.django_db
def test_user_without_permission_cant_view_lease(
    django_db_setup, client, lease_test_data, user_factory
):
    user = user_factory(username="test_user")
    user.set_password("test_password")
    user.save()

    client.login(username="test_user", password="test_password")

    url = reverse("v1:lease-detail", kwargs={"pk": lease_test_data["lease"].id})

    response = client.get(url)

    assert response.status_code == 403, "%s %s" % (response.status_code, response.data)
    assert response.data["detail"].code == "permission_denied"


@pytest.mark.django_db
def test_user_with_permission_can_view_lease(
    django_db_setup, client, lease_test_data, user_factory
):
    user = user_factory(username="test_user")
    user.set_password("test_password")
    user.save()

    permission = Permission.objects.get(codename="view_lease")
    user.user_permissions.add(permission)

    client.login(username="test_user", password="test_password")

    url = reverse("v1:lease-detail", kwargs={"pk": lease_test_data["lease"].id})

    response = client.get(url)

    assert response.status_code == 200, "%s %s" % (response.status_code, response.data)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "field_permissions, expected_keys",
    [
        ([], []),
        (["view_contact_id"], ["id"]),
        (["view_contact_id", "view_contact_name"], ["id", "name"]),
        (["change_contact_id"], ["id"]),
        (["change_contact_id", "change_contact_name"], ["id", "name"]),
        (["view_contact_id", "change_contact_name"], ["id", "name"]),
    ],
)
def test_field_permission(
    django_db_setup,
    client,
    lease_test_data,
    user_factory,
    field_permissions,
    expected_keys,
):
    user = user_factory(username="test_user")
    user.set_password("test_password")
    user.save()

    field_permissions.append("view_contact")

    for field_permission in field_permissions:
        permission = Permission.objects.get(codename=field_permission)
        user.user_permissions.add(permission)

    client.login(username="test_user", password="test_password")

    contact = lease_test_data["tenantcontacts"][0].contact

    url = reverse("v1:contact-detail", kwargs={"pk": contact.id})

    response = client.get(url)

    assert response.status_code == 200, "%s %s" % (response.status_code, response.data)
    assert list(response.data.keys()) == expected_keys
