import pytest
from django.contrib.auth.models import Permission
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from users.models import User


@pytest.mark.django_db
def test_export_lease_area_permission_with_permission():
    user = User.objects.create_user(username="testuser", password="testpassword")
    permission = Permission.objects.get(codename="export_api_lease_area")
    user.user_permissions.add(permission)
    token = Token.objects.create(user=user)

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

    url = reverse("export_v1:export_lease_area-list")
    request = client.get(url)

    assert request.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_export_lease_area_permission_without_permission():
    user = User.objects.create_user(username="testuser", password="testpassword")
    token = Token.objects.create(user=user)

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

    url = reverse("export_v1:export_lease_area-list")
    request = client.get(url)

    assert request.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_export_lease_area_permission_unauthenticated():
    client = APIClient()

    url = reverse("export_v1:export_lease_area-list")
    request = client.get(url)

    assert request.status_code == status.HTTP_401_UNAUTHORIZED
