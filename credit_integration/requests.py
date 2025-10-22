import hashlib
from urllib.parse import urljoin

import requests
from django.conf import settings
from django.utils import timezone

from credit_integration.exceptions import AsiakastietoAPIError
from credit_integration.types import (
    AsiakastietoTarget,
    BusinessId,
    CompanySanctionsQueryParams,
    CompanySanctionsResponse,
    ErrorMessage,
    WatchlistQueryParams,
    WatchListSearchResponse,
)


def request_company_decision(business_id, end_user):
    url = _build_company_decision_url()

    user_id: str = settings.ASIAKASTIETO_USER_ID
    password: str = settings.ASIAKASTIETO_PASSWORD
    key: str = settings.ASIAKASTIETO_KEY
    target: AsiakastietoTarget = settings.ASIAKASTIETO_COMPANY_TARGET_KEY

    timestamp = _get_timestamp()
    checksum = _calculate_checksum(user_id, end_user, timestamp, key)

    headers = {"accept": "application/json"}
    data = (
        f"version=5.01&userid={user_id}&passwd={password}&enduser={end_user}&reqmsg=DECISION"
        f"&qtype=02&model=HEASYR&businessid={business_id}&format=xml&timestamp={timestamp}&checksum={checksum}"
        f"&target={target}"
    )

    response = requests.post(url, data=data, headers=headers)
    return response.json()


def request_consumer_decision(identity_number, end_user):
    url = _build_consumer_decision_url()

    user_id: str = settings.ASIAKASTIETO_USER_ID
    password: str = settings.ASIAKASTIETO_PASSWORD
    key: str = settings.ASIAKASTIETO_KEY
    target: AsiakastietoTarget = settings.ASIAKASTIETO_CONSUMER_TARGET_KEY

    timestamp = _get_timestamp()
    checksum = _calculate_checksum(user_id, end_user, timestamp, key)

    headers = {"accept": "application/json"}
    data = (
        f"version=2018&lang=FI&userid={user_id}&passwd={password}&enduser={end_user}"
        f"&reqmsg=DECISION&qtype=02&model=HEASKU&idnumber={identity_number}&request=H&format=xml"
        f"&timestamp={timestamp}&checksum={checksum}&target={target}"
    )

    response = requests.post(url, data=data, headers=headers)
    return response.json()


def request_company_sanctions(
    end_user: str, business_id: BusinessId = None
) -> CompanySanctionsResponse:
    if business_id is None:
        raise ValueError("Business ID is required for company sanctions request")
    url = _build_company_sanctions_url()

    user_id: str = settings.ASIAKASTIETO_SANCTIONS_USER_ID
    password: str = settings.ASIAKASTIETO_SANCTIONS_PASSWORD
    key: str = settings.ASIAKASTIETO_SANCTIONS_KEY
    target: AsiakastietoTarget = settings.ASIAKASTIETO_COMPANY_TARGET_KEY

    timestamp = _get_timestamp()
    checksum = _calculate_checksum(user_id, end_user, timestamp, key)

    headers = {"accept": "application/json"}
    query_params: CompanySanctionsQueryParams = {
        "version": "5.01",
        "target": target,
        "userid": user_id,
        "passwd": password,
        "enduser": end_user,
        "segment": "A",
        "reqmsg": "COMPANY",
        "format": "json",
        "businessid": business_id,
        "qtype": "DG",
        "listType.listCode": ["SANCTION_LIST"],
        "timestamp": requests.utils.quote(str(timestamp)),
        "checksum": checksum,
        "lang": "FI",
        "format": "json",
    }
    url += f"?{_build_query_parameters(query_params)}"
    response = requests.get(url, headers=headers)
    data: CompanySanctionsResponse = response.json()

    error_message: ErrorMessage = data["companyResponse"].get("errorMessage")
    if error_message is not None:
        raise AsiakastietoAPIError(
            f"Error in company sanctions response: {error_message}"
        )
    return data


def request_consumer_sanctions(
    end_user: str,
    first_name: str = None,
    last_name: str = None,
    birth_year: str = None,
) -> WatchListSearchResponse:
    if last_name is None:
        raise ValueError("`last_name` is required for consumer sanctions request")
    url = _build_consumer_sanctions_url()

    user_id: str = settings.ASIAKASTIETO_SANCTIONS_USER_ID
    password: str = settings.ASIAKASTIETO_SANCTIONS_PASSWORD
    key: str = settings.ASIAKASTIETO_SANCTIONS_KEY
    target: AsiakastietoTarget = settings.ASIAKASTIETO_CONSUMER_TARGET_KEY

    if end_user is None or len(end_user) == 0:
        # This API seems to require end_user not being empty string
        end_user = "test"
    timestamp = _get_timestamp()
    checksum = _calculate_checksum(user_id, end_user, timestamp, key)

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json; charset=utf-8",
    }
    query_params: WatchlistQueryParams = {
        "target": target,
        "userid": user_id,
        "passwd": password,
        "enduser": end_user,
        "entityType": "I",
        "listType.listCode": ["SANCTION_LIST"],
        # "personId": None,  # Not currently using person identity number
        "firstName": first_name,
        "lastName": last_name,
        "birthDate": birth_year,
        "timestamp": requests.utils.quote(str(timestamp)),
        "checksum": checksum,
        "lang": "FI",
        "format": "json",
    }
    url += f"?{_build_query_parameters(query_params)}"

    response = requests.get(url, headers=headers)
    data: WatchListSearchResponse = response.json()
    error_message: ErrorMessage = data["watchListResponse"].get("errorMessage")
    if error_message is not None:
        raise AsiakastietoAPIError(
            f"Error in company sanctions response: {error_message}"
        )
    return data


def _build_query_parameters(
    query_params: CompanySanctionsQueryParams | WatchlistQueryParams,
) -> str:
    """Generates a string of query parameters from a dictionary.
    When duplicate keys are needed, make the keys value a list."""
    params = []
    for key, value in query_params.items():
        if isinstance(value, list):
            # Duplicate queryparam keys in a list, e.g. key1=value1&key1=value2
            for item in value:
                if value is not None:
                    params.append(f"{key}={item}")
        else:
            if value is not None:
                params.append(f"{key}={value}")
    return "&".join(params)


def _build_company_decision_url():
    base_url = settings.ASIAKASTIETO_URL
    url = urljoin(base_url, "services/company5/REST")
    return url


def _build_consumer_decision_url():
    base_url = settings.ASIAKASTIETO_URL
    url = urljoin(base_url, "services/consumer5/REST")
    return url


def _build_company_sanctions_url():
    return _build_company_decision_url()


def _build_consumer_sanctions_url():
    base_url = settings.ASIAKASTIETO_URL
    url = urljoin(base_url, "services/watchlist5/REST")
    return url


def _calculate_checksum(user_id, end_user, timestamp, key):
    hash = bytes(
        "{0}&{1}&{2}&{3}&".format(user_id, end_user, timestamp, key), encoding="utf8"
    )
    return hashlib.sha512(hash).hexdigest().upper()


def _get_timestamp():
    now = timezone.now().astimezone()
    return now.strftime("%Y%m%d%H%M%S%f")[:-4] + now.strftime("%z")[:-2] + "00000"
