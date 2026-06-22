from unittest.mock import ANY, MagicMock, patch

import pytest
import requests
from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings

from integrations.ryyti import (
    DocumentOption,
    NotificationState,
    RegisterOption,
    RyytiClient,
    RyytiException,
)

RYYTI_CONFIG = {
    "AUTH_URL": "https://auth.example.com/token",
    "CLIENT_ID": "test_id",
    "SECRET": "test_secret",
    "USERNAME": "test_user",
    "PASSWORD": "test_password",
    "BASE_URL": "https://api.example.com",
}


@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()


@pytest.fixture
def ryyti_client():
    with override_settings(RYYTI_CONFIG=RYYTI_CONFIG):
        return RyytiClient()


def test_init_success(ryyti_client):
    assert ryyti_client.client_id == "test_id"
    assert ryyti_client.secret == "test_secret"
    assert ryyti_client.base_url == "https://api.example.com"
    assert ryyti_client.auth_url == "https://auth.example.com/token"


def test_init_missing_config():
    with override_settings(RYYTI_CONFIG=None):
        with patch("django.conf.settings", spec=[]):
            with pytest.raises(
                ImproperlyConfigured, match="RYYTI_CONFIG is not defined"
            ):
                RyytiClient()


def test_get_access_token_success(ryyti_client):
    with patch("requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "valid_token",
            "expires_in": 3600,
        }
        mock_post.return_value = mock_response

        token = ryyti_client.get_access_token()

        assert token == "valid_token"
        assert cache.get("ryyti_access_token") == "valid_token"
        mock_post.assert_called_once()


def test_get_access_token_cached(ryyti_client):
    cache.set("ryyti_access_token", "cached_token", 3600)

    with patch("requests.post") as mock_post:
        token = ryyti_client.get_access_token()

        assert token == "cached_token"
        mock_post.assert_not_called()


def test_get_access_token_failure(ryyti_client):
    with patch("requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "Unauthorized"
        )
        mock_post.return_value = mock_response

        with pytest.raises(RyytiException, match="Failed to authenticate"):
            ryyti_client.get_access_token()


def test_get_company_info_success(ryyti_client):
    with patch.object(RyytiClient, "get_access_token", return_value="token"):
        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"name": "Test Company"}
            mock_get.return_value = mock_response

            result = ryyti_client.get_company_info("1234567-8")

            assert result.status_code == 200
            assert result.json() == {"name": "Test Company"}
            mock_get.assert_called_once_with(
                "https://api.example.com/company-basic-data/v1/company",
                headers={
                    "Authorization": "Bearer token",
                    "X-RyytiAuth-ClientCorrelationId": ANY,
                    "Accept": "application/json",
                },
                params={"businessId": "1234567-8"},
                timeout=30,
                stream=False,
            )


def test_get_company_info_404(ryyti_client):
    with patch.object(RyytiClient, "get_access_token", return_value="token"):
        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 404
            # A Response object with status_code 404 is falsy
            mock_response.__bool__.return_value = False
            mock_get.return_value = mock_response

            result = ryyti_client.get_company_info("1234567-8")

            assert result.status_code == 404
            assert not result


def test_get_trade_register_extract_success(ryyti_client):
    with patch.object(RyytiClient, "get_access_token", return_value="token"):
        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"trade_name": "Test Trade Name"}
            mock_get.return_value = mock_response

            result = ryyti_client.get_trade_register_extract_json(
                business_id="1234567-8"
            )

            assert result.status_code == 200
            assert result.json() == {"trade_name": "Test Trade Name"}
            mock_get.assert_called_once_with(
                "https://api.example.com/company-structured-extract/v1/trade-register-extract",
                headers={
                    "Authorization": "Bearer token",
                    "X-RyytiAuth-ClientCorrelationId": ANY,
                    "Accept": "application/json",
                },
                params={"businessId": "1234567-8"},
                timeout=30,
                stream=False,
            )


def test_get_pdf_document_success(ryyti_client):
    with patch.object(RyytiClient, "get_access_token", return_value="token"):
        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.content = b"PDF_CONTENT"
            mock_get.return_value = mock_response

            result = ryyti_client.get_pdf_document(
                document_option=DocumentOption.ORGANISATION_RULES,
                business_id="1234567-8",
                register=RegisterOption.TRADE_REGISTER,
            )

            assert result.status_code == 200
            assert result.content == b"PDF_CONTENT"
            mock_get.assert_called_once_with(
                "https://api.example.com/document-search/v1/documents",
                headers={
                    "Authorization": "Bearer token",
                    "X-RyytiAuth-ClientCorrelationId": ANY,
                    "Accept": "application/pdf",
                },
                params={
                    "businessId": "1234567-8",
                    "register": RegisterOption.TRADE_REGISTER,
                    "documentOption": DocumentOption.ORGANISATION_RULES,
                    "onlyMetadata": "false",
                },
                timeout=30,
                stream=False,
            )


def test_get_exception_handling(ryyti_client):
    with patch.object(RyytiClient, "get_access_token", return_value="token"):
        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
                "Internal Server Error"
            )
            mock_get.return_value = mock_response

            with pytest.raises(RyytiException, match="Ryyti API error"):
                ryyti_client.get_company_info("1234567-8")


def test_get_notifications_success(ryyti_client):
    with patch.object(RyytiClient, "get_access_token", return_value="token"):
        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"notifications": []}
            mock_get.return_value = mock_response

            result = ryyti_client.get_notifications(
                business_id="1234567-8",
                notification_state=NotificationState.PENDING,
                stream=True,
            )

            assert result.status_code == 200
            assert result.json() == {"notifications": []}
            mock_get.assert_called_once_with(
                "https://api.example.com/notification-search/v1/notifications",
                headers={
                    "Authorization": "Bearer token",
                    "X-RyytiAuth-ClientCorrelationId": ANY,
                    "Accept": "application/json",
                },
                params={
                    "businessId": "1234567-8",
                    "notificationState": NotificationState.PENDING,
                },
                timeout=30,
                stream=True,
            )


def test_get_trade_register_extract_json_validation(ryyti_client):
    with pytest.raises(
        ValueError, match="Either business_id or registration_number must be provided."
    ):
        ryyti_client.get_trade_register_extract_json()

    with pytest.raises(
        ValueError,
        match="Only one of business_id or registration_number should be provided, not both.",
    ):
        ryyti_client.get_trade_register_extract_json(
            business_id="1234567-8", registration_number="1.234.567"
        )


def test_get_trade_register_extract_pdf_success(ryyti_client):
    with patch.object(RyytiClient, "get_access_token", return_value="token"):
        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.content = b"PDF_CONTENT"
            mock_get.return_value = mock_response

            result = ryyti_client.get_trade_register_extract_pdf(
                business_id="1234567-8"
            )

            assert result.status_code == 200
            assert result.content == b"PDF_CONTENT"
            mock_get.assert_called_once_with(
                "https://api.example.com/generate-extract/v1/trade-register-extract",
                headers={
                    "Authorization": "Bearer token",
                    "X-RyytiAuth-ClientCorrelationId": ANY,
                    "Accept": "application/pdf",
                },
                params={"businessId": "1234567-8"},
                timeout=30,
                stream=False,
            )


def test_get_trade_register_extract_pdf_validation(ryyti_client):
    with pytest.raises(
        ValueError, match="Either business_id or registration_number must be provided."
    ):
        ryyti_client.get_trade_register_extract_pdf()

    with pytest.raises(
        ValueError,
        match="Only one of business_id or registration_number should be provided, not both.",
    ):
        ryyti_client.get_trade_register_extract_pdf(
            business_id="1234567-8", registration_number="1.234.567"
        )
