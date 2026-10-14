import pytest
from django.urls import reverse
from rest_framework import status

from landuse.models.agreement import (
    AgreementAddress,
    DetailedPlan,
    District,
    LandUseAgreement,
)
from landuse.models.party import AgreementParty, ContactPerson

pytestmark = [pytest.mark.django_db, pytest.mark.usefixtures("admin_client")]


@pytest.fixture(autouse=True)
def enable_landuse_api(settings):
    settings.FLAG_LANDUSE_API_ENABLED = True


def test_agreement_list_uses_compact_representation(admin_client):
    district = District.objects.create(name="Kallio", identifier="11")
    agreement = LandUseAgreement.objects.create(
        identifier="M-2026-1", district=district
    )

    response = admin_client.get(reverse("v1:landuse:agreement-list"))

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["results"][0]["id"] == agreement.pk
    assert response.json()["results"][0]["district"] == {
        "id": district.pk,
        "name": "Kallio",
        "identifier": "11",
    }
    assert "collateral_multiplier" not in response.json()["results"][0]


def test_detailed_plan_list_is_paginated(admin_client):
    for index in range(101):
        DetailedPlan.objects.create(plan_number=str(index))

    response = admin_client.get(reverse("v1:landuse:detailed-plan-list"))

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["count"] == 101
    assert len(response.json()["results"]) == 100
    assert response.json()["next"] is not None


def test_overview_and_parties_are_separate_tab_documents(admin_client):
    agreement = LandUseAgreement.objects.create(identifier="M-2026-1")
    AgreementAddress.objects.create(
        agreement=agreement,
        street_address="Testikatu 1",
        postal_code="00100",
        city="Helsinki",
    )
    party = AgreementParty.objects.create(agreement=agreement, name="Test Oy")
    ContactPerson.objects.create(agreement_party=party, name="Test Person")

    overview_response = admin_client.get(
        reverse("v1:landuse:agreement-overview", args=(agreement.pk,))
    )
    parties_response = admin_client.get(
        reverse("v1:landuse:agreement-parties", args=(agreement.pk,))
    )

    assert overview_response.status_code == status.HTTP_200_OK
    assert overview_response.json()["addresses"][0]["street_address"] == "Testikatu 1"
    assert parties_response.status_code == status.HTTP_200_OK
    assert parties_response.json()["count"] == 1
    assert parties_response.json()["results"][0]["name"] == "Test Oy"
    assert (
        parties_response.json()["results"][0]["contact_persons"][0]["name"]
        == "Test Person"
    )
