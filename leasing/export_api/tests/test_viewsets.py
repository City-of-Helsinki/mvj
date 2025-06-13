import pytest
from django.contrib.auth.models import Permission
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from users.models import User


@pytest.mark.parametrize(
    "urlname,permission_codename",
    [
        ("export_v1:export_lease_area-list", "export_api_lease_area"),
        ("export_v1:export_vipunen_map_layer-list", "export_api_vipunen_map_layer"),
        (
            "export_v1:export_lease_statistic_report-list",
            "export_api_lease_statistic_report",
        ),
        ("export_v1:export_expired_lease-list", "export_api_expired_lease"),
    ],
)
@pytest.mark.django_db
def test_export_endpoint_permission_with_permission(urlname, permission_codename):
    user = User.objects.create_user(username="testuser", password="testpassword")
    permission = Permission.objects.get(codename=permission_codename)
    user.user_permissions.add(permission)
    token = Token.objects.create(user=user)

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

    url = reverse(urlname)
    request = client.get(url)

    assert request.status_code == status.HTTP_200_OK


@pytest.mark.parametrize(
    "urlname",
    [
        "export_v1:export_lease_area-list",
        "export_v1:export_vipunen_map_layer-list",
        "export_v1:export_lease_statistic_report-list",
        "export_v1:export_expired_lease-list",
    ],
)
@pytest.mark.django_db
def test_export_endpoint_permission_without_permission(urlname):
    user = User.objects.create_user(username="testuser", password="testpassword")
    token = Token.objects.create(user=user)

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

    url = reverse(urlname)
    request = client.get(url)

    assert request.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.parametrize(
    "urlname",
    [
        "export_v1:export_lease_area-list",
        "export_v1:export_vipunen_map_layer-list",
        "export_v1:export_lease_statistic_report-list",
        "export_v1:export_expired_lease-list",
    ],
)
@pytest.mark.django_db
def test_export_endpoint_permission_unauthenticated(urlname):
    client = APIClient()

    url = reverse(urlname)
    request = client.get(url)

    assert request.status_code == status.HTTP_401_UNAUTHORIZED
