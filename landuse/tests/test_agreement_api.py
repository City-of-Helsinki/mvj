import pytest
from django.urls import reverse
from rest_framework import status

from landuse.models.agreement import (
    AgreementAddress,
    AgreementPreparer,
    AuthorizedSignatory,
    DetailedPlan,
    District,
    LandUseAgreement,
)
from landuse.models.compensation import LandPolicyProgram
from landuse.models.contract import Contract
from landuse.models.decision import Decision
from landuse.models.party import AgreementParty, ContactPerson
from landuse.models.site import SiteIntendedUse, SiteTenureType

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
    agreement = LandUseAgreement.objects.create(
        identifier="M-2026-1", detailed_plan_sites=["91-10-100-1"]
    )
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
    assert overview_response.json()["detailed_plan_sites"] == ["91-10-100-1"]
    assert parties_response.status_code == status.HTTP_200_OK
    assert parties_response.json()["count"] == 1
    assert parties_response.json()["results"][0]["name"] == "Test Oy"
    assert (
        parties_response.json()["results"][0]["contact_persons"][0]["name"]
        == "Test Person"
    )


def test_agreement_updates_detailed_plan_sites(admin_client):
    agreement = LandUseAgreement.objects.create(identifier="M-2026-1")

    response = admin_client.patch(
        reverse("v1:landuse:agreement-detail", args=(agreement.pk,)),
        {"detailed_plan_sites": ["91-10-100-1", "91-10-100-2"]},
        content_type="application/json",
    )

    agreement.refresh_from_db()
    assert response.status_code == status.HTTP_200_OK
    assert agreement.detailed_plan_sites == ["91-10-100-1", "91-10-100-2"]


def test_referenced_decision_is_preserved_when_replacing_decisions(admin_client):
    agreement = LandUseAgreement.objects.create(identifier="MA101-1")
    decision = Decision.objects.create(agreement=agreement)
    contract = Contract.objects.create(agreement=agreement, decision=decision)

    response = admin_client.put(
        reverse("v1:landuse:agreement-decisions", args=(agreement.pk,)),
        [],
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert Decision.objects.filter(pk=decision.pk).exists()
    assert Contract.objects.filter(pk=contract.pk).exists()


def test_summary_saves_relationships_and_collections(admin_client, user_factory):
    agreement = LandUseAgreement.objects.create(identifier="MA101-2")
    preparer = user_factory()
    signatory = AuthorizedSignatory.objects.create(name="Signatory")
    plan = DetailedPlan.objects.create(plan_number="12345")

    response = admin_client.patch(
        reverse("v1:landuse:agreement-detail", args=(agreement.pk,)),
        {
            "authorized_signatory": signatory.pk,
            "detailed_plan": plan.pk,
            "addresses": [
                {
                    "street_address": "Testikatu 1",
                    "postal_code": "00100",
                    "city": "Helsinki",
                }
            ],
            "preparers": [{"preparer": preparer.pk}],
        },
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_200_OK
    assert agreement.addresses.get().street_address == "Testikatu 1"
    assert agreement.preparers.get().preparer_id == preparer.pk


def test_compensation_and_sites_accept_related_object_ids(admin_client):
    agreement = LandUseAgreement.objects.create(identifier="M-2026-1")
    land_policy_program = LandPolicyProgram.objects.create(name="MAPO2")
    intended_use = SiteIntendedUse.objects.create(name="Residential")
    tenure_type = SiteTenureType.objects.create(name="Rental")

    compensation_response = admin_client.put(
        reverse("v1:landuse:agreement-compensation", args=(agreement.pk,)),
        {
            "land_policy_program": land_policy_program.pk,
            "land_policy_program_discount_percentage": "25",
        },
        content_type="application/json",
    )
    sites_response = admin_client.put(
        reverse("v1:landuse:agreement-sites", args=(agreement.pk,)),
        [
            {
                "identifier": "91-10-100-1",
                "intended_use": intended_use.pk,
                "tenure_types": [tenure_type.pk],
            }
        ],
        content_type="application/json",
    )

    assert compensation_response.status_code == status.HTTP_200_OK
    assert compensation_response.json()["land_policy_program"] == {
        "id": land_policy_program.pk,
        "name": "MAPO2",
        "default_discount_percentage": None,
    }
    assert sites_response.status_code == status.HTTP_200_OK
    assert sites_response.json()[0]["intended_use"] == {
        "id": intended_use.pk,
        "name": "Residential",
    }
    assert sites_response.json()[0]["tenure_types"] == [
        {"id": tenure_type.pk, "name": "Rental"}
    ]
