import datetime
import hashlib
from urllib.parse import urljoin

import requests
from django.conf import settings


def request_company_decision(business_id, end_user):
    url = _build_company_decision_url()

    user_id = settings.ASIAKASTIETO_USER_ID
    password = settings.ASIAKASTIETO_PASSWORD
    key = settings.ASIAKASTIETO_KEY

    timestamp = _get_timestamp()
    checksum = _calculate_checksum(user_id, end_user, timestamp, key)

    headers = {"accept": "application/json"}
    data = (
        f"version=5.01&userid={user_id}&passwd={password}&enduser={end_user}&reqmsg=DECISION"
        f"&qtype=02&model=HEASYR&businessid={business_id}&format=xml&timestamp={timestamp}&checksum={checksum}"
        f"&target=VAP1"
    )

    response = requests.post(url, data=data, headers=headers)
    return response.json()


def request_consumer_decision(identity_number, end_user):
    url = _build_consumer_decision_url()

    user_id = settings.ASIAKASTIETO_USER_ID
    password = settings.ASIAKASTIETO_PASSWORD
    key = settings.ASIAKASTIETO_KEY

    timestamp = _get_timestamp()
    checksum = _calculate_checksum(user_id, end_user, timestamp, key)

    headers = {"accept": "application/json"}
    data = (
        f"version=2018&lang=FI&userid={user_id}&passwd={password}&enduser={end_user}"
        f"&reqmsg=DECISION&qtype=02&model=HEASKU&idnumber={identity_number}&request=H&format=xml"
        f"&timestamp={timestamp}&checksum={checksum}&target=TAP1"
    )

    response = requests.post(url, data=data, headers=headers)
    return response.json()


def _build_company_decision_url():
    base_url = settings.ASIAKASTIETO_URL
    url = urljoin(base_url, "services/company5/REST")
    return url


def _build_consumer_decision_url():
    base_url = settings.ASIAKASTIETO_URL
    url = urljoin(base_url, "services/consumer5/REST")
    return url


def _calculate_checksum(user_id, end_user, timestamp, key):
    hash = bytes(
        "{0}&{1}&{2}&{3}&".format(user_id, end_user, timestamp, key), encoding="utf8"
    )
    return hashlib.sha512(hash).hexdigest().upper()


def _get_timestamp():
    now = datetime.datetime.now().astimezone()
    return now.strftime("%Y%m%d%H%M%S%f")[:-4] + now.strftime("%z")[:-2] + "00000"
