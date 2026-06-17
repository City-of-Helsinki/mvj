from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth.models import Permission
from django.urls import reverse
from rest_framework import status

from integrations.ryyti import MediaType


@pytest.fixture
def dummy_ryyti_config(settings):
    settings.RYYTI_CONFIG = {
        "AUTH_URL": "https://auth.example.com/token",
        "CLIENT_ID": "test_id",
        "SECRET": "test_secret",
        "USERNAME": "test_user",
        "PASSWORD": "test_password",
        "BASE_URL": "https://api.example.com",
    }


@pytest.fixture
def user_with_perm(django_user_model):
    user = django_user_model.objects.create_user(username="testuser")
    permission = Permission.objects.get(codename="view_invoice")
    user.user_permissions.add(permission)
    return user


@pytest.fixture
def user_without_perm(django_user_model):
    return django_user_model.objects.create_user(username="nopermuser")


@pytest.mark.django_db
def test_ryyti_proxy_unknown_api(client, user_with_perm, dummy_ryyti_config):
    client.force_login(user_with_perm)
    url = reverse(
        "ryyti-api-proxy", kwargs={"api": "unknown_service", "business_id": "1234567-8"}
    )
    response = client.get(url)
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "Unknown API" in str(response.data)


@pytest.mark.django_db
def test_ryyti_proxy_no_permission(client, user_without_perm, dummy_ryyti_config):
    client.force_login(user_without_perm)
    url = reverse(
        "ryyti-api-proxy",
        kwargs={"api": "organisation_rules_pdf", "business_id": "1234567-8"},
    )
    response = client.get(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
@patch("leasing.views.RyytiClient")
def test_ryyti_proxy_pdf_success(
    mock_client_class, client, user_with_perm, dummy_ryyti_config
):
    client.force_login(user_with_perm)
    mock_client = mock_client_class.return_value
    mock_api_response = MagicMock()
    mock_api_response.status_code = 200
    mock_api_response.headers = {"Content-Type": MediaType.PDF}
    mock_api_response.iter_content.return_value = [b"pdf-content"]

    mock_client.get_pdf_document.return_value = mock_api_response

    url = reverse(
        "ryyti-api-proxy",
        kwargs={"api": "organisation_rules_pdf", "business_id": "1234567-8"},
    )
    response = client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.get("Content-Type") == MediaType.PDF
    assert "inline" in response.get("Content-Disposition")
    assert b"".join(response.streaming_content) == b"pdf-content"


@pytest.mark.django_db
@patch("leasing.views.RyytiClient")
def test_ryyti_proxy_json_success(
    mock_client_class, client, user_with_perm, dummy_ryyti_config
):
    client.force_login(user_with_perm)
    mock_client = mock_client_class.return_value
    mock_api_response = MagicMock()
    mock_api_response.status_code = 200
    mock_api_response.headers = {"Content-Type": MediaType.JSON}
    mock_api_response.iter_content.return_value = [b'{"foo": "bar"}']

    # Check which method is called for company_info
    mock_client.get_company_info.return_value = mock_api_response

    url = reverse(
        "ryyti-api-proxy",
        kwargs={"api": "company_info_json", "business_id": "1234567-8"},
    )
    response = client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.get("Content-Type") == MediaType.JSON
    assert "Content-Disposition" not in response
    assert b"".join(response.streaming_content) == b'{"foo": "bar"}'


@pytest.mark.django_db
@patch("leasing.views.RyytiClient")
def test_ryyti_proxy_upstream_error(
    mock_client_class, client, user_with_perm, dummy_ryyti_config
):
    client.force_login(user_with_perm)
    mock_client = mock_client_class.return_value
    mock_api_response = MagicMock()
    mock_api_response.status_code = 404

    mock_client.get_company_info.return_value = mock_api_response

    url = reverse(
        "ryyti-api-proxy",
        kwargs={"api": "company_info_json", "business_id": "1234567-8"},
    )
    response = client.get(url)

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "Data not available" in str(response.data)
