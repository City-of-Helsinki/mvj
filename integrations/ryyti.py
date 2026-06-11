import base64
from enum import StrEnum
from typing import Annotated, Any, Required, TypeAlias, TypedDict
from uuid import uuid4

import requests
from django.conf import LazySettings, settings
from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured

RYYTI_ACCESS_TOKEN_CACHE_KEY = "ryyti_access_token"


class RyytiException(Exception):
    """Base exception for Ryyti API integration."""


class RyytiConfig(TypedDict):
    AUTH_URL: Required[str]
    CLIENT_ID: Required[str]
    SECRET: Required[str]
    USERNAME: Required[str]
    PASSWORD: Required[str]
    BASE_URL: Required[str]


class DjangoSettingsWithRyytiConfig(LazySettings):
    RYYTI_CONFIG: "RyytiConfig"


class DocumentOption(StrEnum):
    ORGANISATION_RULES = "Y"
    NOTIFICATION_DOCUMENTS = "I"


class RegisterOption(StrEnum):
    TRADE_REGISTER = "KREK"
    REGISTER_OF_FOUNDATIONS = "SREK"


ResponseData: TypeAlias = dict[str, Any]

DateISOStr: TypeAlias = str  # Format: YYYY-MM-DD


class RyytiClient:
    auth_url: str
    client_id: str
    secret: str
    username: str
    password: str
    base_url: str

    def __init__(self) -> None:
        try:
            ryyti_config: RyytiConfig = getattr(settings, "RYYTI_CONFIG")
        except AttributeError:
            ryyti_config = None  # type: ignore

        if not ryyti_config:
            raise ImproperlyConfigured(
                "RYYTI_CONFIG is not defined in Django settings."
            )

        required_settings = (
            "AUTH_URL",
            "CLIENT_ID",
            "SECRET",
            "USERNAME",
            "PASSWORD",
            "BASE_URL",
        )

        missing = [
            key
            for key in required_settings
            if not isinstance(value := ryyti_config.get(key), str) or not value.strip()
        ]

        if missing:
            raise ImproperlyConfigured(
                f"RyytiClient is missing required settings: {', '.join(missing)}. "
                f"Check RYYTI_CONFIG in Django settings."
            )

        self.auth_url = ryyti_config["AUTH_URL"]
        self.client_id = ryyti_config["CLIENT_ID"]
        self.secret = ryyti_config["SECRET"]
        self.username = ryyti_config["USERNAME"]
        self.password = ryyti_config["PASSWORD"]
        self.base_url = ryyti_config["BASE_URL"]

    def get_access_token(self) -> str:
        token: str | None = cache.get(RYYTI_ACCESS_TOKEN_CACHE_KEY)
        if token is None:
            self._authenticate()
            token = cache.get(RYYTI_ACCESS_TOKEN_CACHE_KEY)
        return token

    def _authenticate(self) -> None:
        auth_header = f"{self.client_id}:{self.secret}".encode("utf-8")
        auth_header_b64 = base64.b64encode(auth_header).decode("utf-8")

        try:
            response = requests.post(
                self.auth_url,
                headers={
                    "Accept": "application/json",
                    "Authorization": f"Basic {auth_header_b64}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data={
                    "grant_type": "password",
                    "username": self.username,
                    "password": self.password,
                    "scope": "openid profile email group_membership",
                },
                timeout=30,
            )
            response.raise_for_status()
        except requests.RequestException as e:
            raise RyytiException(f"Failed to authenticate with Ryyti: {e}") from e

        auth_response = response.json()
        token, expires_in = auth_response.get("access_token"), auth_response.get(
            "expires_in"
        )

        if token is None:
            raise RyytiException("Ryyti authentication response missing access_token")
        if expires_in is None or expires_in <= 0:
            raise RyytiException("Ryyti authentication response missing expires_in")

        expire_time = max(
            60, expires_in - 60
        )  # Subtract 60 seconds to ensure token is refreshed before it expires

        cache.set(RYYTI_ACCESS_TOKEN_CACHE_KEY, token, timeout=expire_time)

    def _get(self, url: str, params: dict[str, str] | None = None) -> ResponseData:
        token = self.get_access_token()
        client_correlation_id = uuid4()
        try:
            response = requests.get(
                url,
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-RyytiAuth-ClientCorrelationId": str(client_correlation_id),
                    "Accept": "application/json",
                },
                params=params,
                timeout=30,
            )
            if response.status_code == 404:
                return {}
            response.raise_for_status()
        except requests.RequestException as e:
            raise RyytiException(f"Ryyti API error: {e}") from e

        response_data: ResponseData = response.json()
        return response_data

    def _get_pdf(self, url: str, params: dict[str, str] | None = None) -> bytes:
        token = self.get_access_token()
        client_correlation_id = uuid4()
        try:
            response = requests.get(
                url,
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-RyytiAuth-ClientCorrelationId": str(client_correlation_id),
                    "Accept": "application/pdf",
                },
                params=params,
                timeout=30,
            )
            if response.status_code == 404:
                return b""
            response.raise_for_status()
        except requests.RequestException as e:
            raise RyytiException(f"Ryyti API error: {e}") from e

        return response.content

    def get_company_info(self, business_id: str) -> ResponseData:
        if not business_id:
            raise ValueError("business_id must be provided.")
        url = f"{self.base_url}/company-basic-data/v1/company"
        params = {"businessId": business_id}
        response = self._get(url, params=params)
        return response

    def get_trade_register_extract(
        self, business_id: str | None = None, registration_number: str | None = None
    ) -> object:
        if not any([business_id, registration_number]):
            raise ValueError(
                "Either business_id or registration_number must be provided."
            )
        url = f"{self.base_url}/company-structured-extract/v1/trade-register-extract"
        raw_params = {
            "businessId": business_id,
            "registrationNumber": registration_number,
        }
        params = {k: v for k, v in raw_params.items() if v is not None}
        response = self._get(url, params=params)
        return response

    def get_pdf_document(
        self,
        document_option: DocumentOption,
        register: RegisterOption = RegisterOption.TRADE_REGISTER,
        only_metadata: bool = False,
        business_id: str | None = None,
        registration_number: Annotated[str | None, "Format: 1.234.567"] = None,
        notification_record_number: Annotated[str | None, "Format: 2024/123456"] = None,
        date: Annotated[DateISOStr | None, "Format: YYYY-MM-DD"] = None,
    ) -> bytes:
        if not all([document_option, register]):
            raise ValueError("Both document_option and register must be provided.")

        if not any([business_id, registration_number]):
            raise ValueError(
                "Either business_id or registration_number must be provided."
            )
        url = f"{self.base_url}/document-search/v1/document"
        raw_params = {
            "businessId": business_id,
            "register": register,
            "documentOption": document_option,
            "onlyMetadata": str(only_metadata).lower(),
            "registrationNumber": registration_number,
            "notificationRecordNumber": notification_record_number,
            "date": date,
        }
        params = {k: v for k, v in raw_params.items() if v is not None}
        response = self._get_pdf(url, params=params)

        return response
