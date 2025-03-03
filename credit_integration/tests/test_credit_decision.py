from io import BytesIO
from unittest.mock import patch

import pytest
from django.contrib.auth.models import Permission
from django.test import override_settings
from django.urls import reverse
from pypdf import PdfReader  # via xhtml2pdf
from rest_framework import status

from credit_integration.enums import CreditDecisionStatus
from credit_integration.models import CreditDecision, CreditDecisionLog
from credit_integration.tests.mocks import (
    mock_return_company_json_data,
    mock_return_company_sanctions_json_data,
    mock_return_consumer_json_data,
    mock_return_consumer_sanctions_json_data,
)
from leasing.enums import ContactType


def _extract_text_from_pdf(pdf_content):
    pdf_reader = PdfReader(BytesIO(pdf_content))
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text


@pytest.mark.django_db
def test_get_credit_decisions_endpoint(
    client,
    user_factory,
    credit_decision_reason_factory,
    business_credit_decision_factory,
):
    user = user_factory()
    password = "test"
    user.set_password(password)
    user.save()
    client.login(username=user.username, password=password)

    permission_names = [
        "view_creditdecision",
    ]

    for permission_name in permission_names:
        user.user_permissions.add(Permission.objects.get(codename=permission_name))

    business_id = "12345678"
    business_credit_decision_factory(
        business_id=business_id,
        reasons=(credit_decision_reason_factory(), credit_decision_reason_factory()),
    )

    data = {"business_id": business_id}
    response = client.get(
        reverse("v1:credit_integration:get-credit-decisions"), data=data, format="json"
    )

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_get_credit_decisions_without_access_right(
    client,
    user_factory,
    credit_decision_reason_factory,
    business_credit_decision_factory,
):
    user = user_factory()
    password = "test"
    user.set_password(password)
    user.save()
    client.login(username=user.username, password=password)

    business_id = "12345678"
    business_credit_decision_factory(
        business_id=business_id,
        reasons=(credit_decision_reason_factory(), credit_decision_reason_factory()),
    )

    data = {"business_id": business_id}
    response = client.get(
        reverse("v1:credit_integration:get-credit-decisions"), data=data, format="json"
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_send_credit_decision_inquiry_endpoint_with_business_id(
    client,
    user_factory,
):
    user_first_name = "John"
    user_last_name = "Doe"
    user = user_factory(first_name=user_first_name, last_name=user_last_name)
    password = "test"
    user.set_password(password)
    user.save()

    permission_names = [
        "send_creditdecision_inquiry",
    ]

    for permission_name in permission_names:
        user.user_permissions.add(Permission.objects.get(codename=permission_name))

    client.login(username=user.username, password=password)

    business_id = "12345678"

    data = {"business_id": business_id}

    with patch(
        "credit_integration.views.request_company_decision",
        return_value=mock_return_company_json_data(business_id),
    ):
        response = client.post(
            reverse("v1:credit_integration:send-credit-decision-inquiry"),
            data=data,
            format="json",
        )

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1
    assert "id" in response.data[0]

    result_credit_decision_id = response.data[0]["id"]
    result_credit_decision = CreditDecision.objects.get(pk=result_credit_decision_id)
    assert result_credit_decision.status == CreditDecisionStatus.CONSIDERATION
    assert result_credit_decision.reasons.count() == 2
    assert result_credit_decision.business_id == business_id
    assert result_credit_decision.official_name
    assert result_credit_decision.address
    assert result_credit_decision.phone_number
    assert result_credit_decision.industry_code
    assert result_credit_decision.claimant == user
    assert result_credit_decision.original_data
    assert CreditDecisionLog.objects.count() == 1


@pytest.mark.django_db
def test_send_credit_decision_inquiry_endpoint_with_identity_number(
    client,
    user_factory,
):
    user_first_name = "John"
    user_last_name = "Doe"
    user = user_factory(first_name=user_first_name, last_name=user_last_name)
    password = "test"
    user.set_password(password)
    user.save()

    permission_names = [
        "send_creditdecision_inquiry",
    ]

    for permission_name in permission_names:
        user.user_permissions.add(Permission.objects.get(codename=permission_name))

    client.login(username=user.username, password=password)

    identity_number = "011213-1234"

    data = {"identity_number": identity_number}

    with patch(
        "credit_integration.views.request_consumer_decision",
        return_value=mock_return_consumer_json_data(identity_number),
    ):
        response = client.post(
            reverse("v1:credit_integration:send-credit-decision-inquiry"),
            data=data,
            format="json",
        )

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1
    assert "id" not in response.data[0]

    assert response.data[0]["status"] == CreditDecisionStatus.NO.value
    assert response.data[0]["claimant"]["first_name"] == "John"
    assert response.data[0]["claimant"]["last_name"] == "Doe"
    assert CreditDecisionLog.objects.count() == 1


@pytest.mark.django_db
def test_send_credit_decision_inquiry_endpoint_with_person_contact(
    client, user_factory, contact_factory
):
    user_first_name = "John"
    user_last_name = "Doe"
    user = user_factory(first_name=user_first_name, last_name=user_last_name)
    password = "test"
    user.set_password(password)
    user.save()

    permission_names = [
        "send_creditdecision_inquiry",
    ]

    for permission_name in permission_names:
        user.user_permissions.add(Permission.objects.get(codename=permission_name))

    client.login(username=user.username, password=password)

    contact = contact_factory(
        first_name="Jane",
        last_name="Doe",
        type=ContactType.PERSON,
        national_identification_number="011213-1234",
    )
    data = {"customer_id": contact.id}

    with patch(
        "credit_integration.views.request_consumer_decision",
        return_value=mock_return_consumer_json_data(
            contact.national_identification_number
        ),
    ):
        response = client.post(
            reverse("v1:credit_integration:send-credit-decision-inquiry"),
            data=data,
            format="json",
        )

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1
    assert "id" not in response.data[0]

    assert response.data[0]["status"] == CreditDecisionStatus.NO.value
    assert response.data[0]["claimant"]["first_name"] == "John"
    assert response.data[0]["claimant"]["last_name"] == "Doe"
    assert CreditDecisionLog.objects.count() == 1


@pytest.mark.django_db
def test_send_credit_decision_inquiry_endpoint_without_access_right(
    client,
    user_factory,
    credit_decision_reason_factory,
    business_credit_decision_factory,
):
    user = user_factory()
    password = "test"
    user.set_password(password)
    user.save()

    client.login(username=user.username, password=password)

    business_id = "12345678"
    business_credit_decision_factory(
        business_id=business_id,
        reasons=(credit_decision_reason_factory(), credit_decision_reason_factory()),
    )

    data = {"business_id": business_id}
    response = client.post(
        reverse("v1:credit_integration:send-credit-decision-inquiry"),
        data=data,
        format="json",
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


@override_settings(FLAG_SANCTIONS_INQUIRY=True)
@pytest.mark.django_db
def test_send_send_sanctions_inquiry_endpoint_with_business_id(
    client,
    user_factory,
):
    user_first_name = "Firstname"
    user_last_name = "Lastname"
    user = user_factory(first_name=user_first_name, last_name=user_last_name)
    password = "test"
    user.set_password(password)
    user.save()

    permission_names = [
        "send_sanctions_inquiry",
    ]

    for permission_name in permission_names:
        user.user_permissions.add(Permission.objects.get(codename=permission_name))

    client.login(username=user.username, password=password)

    business_id = "1234567-8"

    data = {"business_id": business_id}
    mock_response = mock_return_company_sanctions_json_data()
    with patch(
        "credit_integration.views.request_company_sanctions",
        return_value=mock_response,
    ):
        response = client.get(
            reverse("v1:credit_integration:send-sanctions-inquiry"),
            data=data,
        )

    assert response.status_code == status.HTTP_200_OK
    assert response.headers.get("Content-Type") == "application/pdf"
    assert int(response.headers.get("Content-Length")) > 3000

    pdf_content = b"".join(response.streaming_content)
    pdf_text = _extract_text_from_pdf(pdf_content)
    watchlist_hits = mock_response["companyResponse"]["pepAndSanctionsData"][
        "watchListHits"
    ]
    hit1, non_hit2 = watchlist_hits
    assert hit1["hitsRow"][0]["names"]["name"] in pdf_text  # "SANCTIONED COMPANY OY"
    assert non_hit2["name"] in pdf_text  # "Doe, John"


@override_settings(FLAG_SANCTIONS_INQUIRY=True)
@pytest.mark.django_db
def test_send_send_sanctions_inquiry_endpoint_with_last_name(client, user_factory):
    user_first_name = "Firstname"
    user_last_name = "Lastname"
    user = user_factory(first_name=user_first_name, last_name=user_last_name)
    password = "test"
    user.set_password(password)
    user.save()

    permission_names = [
        "send_sanctions_inquiry",
    ]

    for permission_name in permission_names:
        user.user_permissions.add(Permission.objects.get(codename=permission_name))

    client.login(username=user.username, password=password)

    data = {"last_name": "Doe"}

    mock_response = mock_return_consumer_sanctions_json_data()
    with patch(
        "credit_integration.views.request_consumer_sanctions",
        return_value=mock_response,
    ):
        response = client.get(
            reverse("v1:credit_integration:send-sanctions-inquiry"),
            data=data,
        )
    assert response.status_code == status.HTTP_200_OK
    assert response.headers.get("Content-Type") == "application/pdf"
    assert int(response.headers.get("Content-Length")) > 5000
    pdf_content = b"".join(response.streaming_content)
    pdf_text = _extract_text_from_pdf(pdf_content)
    category0 = mock_response["watchListResponse"]["watchLists"]["category"][0]
    hitrow1, hitrow2 = category0["watchListHits"]["hitsRow"]
    assert hitrow1["names"]["name"] in pdf_text  # "Doe, John Michael"
    assert category0["watchListType"] in pdf_text  # "SANCTION_LIST"
    assert (
        hitrow2["description"] in pdf_text
    )  # "Sanctioned Entity. Son of John Michael Doe, Former President Doeland."


@override_settings(FLAG_SANCTIONS_INQUIRY=True)
@pytest.mark.django_db
def test_send_send_sanctions_inquiry_endpoint_without_access_right(
    client,
    user_factory,
):
    user = user_factory()
    password = "test"
    user.set_password(password)
    user.save()

    client.login(username=user.username, password=password)

    business_id = "1234567-8"

    data = {"business_id": business_id}
    response = client.get(
        reverse("v1:credit_integration:send-sanctions-inquiry"),
        data=data,
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


@override_settings(FLAG_SANCTIONS_INQUIRY=True)
@pytest.mark.django_db
def test_send_send_sanctions_inquiry_endpoint_disallowed_method(
    client,
    user_factory,
):
    user = user_factory()
    password = "test"
    user.set_password(password)
    user.save()
    permission_names = [
        "send_sanctions_inquiry",
    ]

    for permission_name in permission_names:
        user.user_permissions.add(Permission.objects.get(codename=permission_name))

    client.login(username=user.username, password=password)

    business_id = "1234567-8"

    data = {"business_id": business_id}
    response = client.post(
        reverse("v1:credit_integration:send-sanctions-inquiry"),
        data=data,
    )

    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
