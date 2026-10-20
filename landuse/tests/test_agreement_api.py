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


def test_agreement_list_includes_searchable_related_fields(admin_client):
    plan = DetailedPlan.objects.create(plan_number="12345")
    agreement = LandUseAgreement.objects.create(
        identifier="MA101-3",
        detailed_plan=plan,
        detailed_plan_sites=["91-1-1-1"],
        is_promotion_area=True,
    )
    AgreementParty.objects.create(agreement=agreement, name="Test Oy")
    row = admin_client.get(reverse("v1:landuse:agreement-list")).json()["results"][0]
    assert row["party_names"] == ["Test Oy"]
    assert row["detailed_plan_number"] == "12345"
    assert row["detailed_plan_sites"] == ["91-1-1-1"]
    assert row["is_promotion_area"] is True


def test_creation_allocates_identifiers_using_district_code(admin_client):
    district = District.objects.create(name="Kallio", identifier="11")
    url = reverse("v1:landuse:agreement-list")
    first = admin_client.post(
        url,
        {"district": district.pk, "municipality": "1"},
        content_type="application/json",
    )
    second = admin_client.post(
        url,
        {"district": district.pk, "municipality": "1"},
        content_type="application/json",
    )
    assert first.status_code == status.HTTP_201_CREATED
    assert first.json()["identifier"] == "MA111-1"
    assert second.json()["identifier"] == "MA111-2"


def test_contracts_save_amendments_and_collateral(admin_client):
    agreement = LandUseAgreement.objects.create(identifier="MA101-4")
    party = AgreementParty.objects.create(agreement=agreement)
    response = admin_client.put(
        reverse("v1:landuse:agreement-contracts", args=(agreement.pk,)),
        [
            {
                "identifier": "C1",
                "contract_type": "LAND_USE_AGREEMENT",
                "changes": [{"identifier": "C1-A1"}],
                "cash_deposit_collaterals": [
                    {
                        "guarantee_type": "CASH_DEPOSIT",
                        "parties": [party.pk],
                        "amount": "100.00",
                    }
                ],
            }
        ],
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK
    contract = agreement.contracts.get()
    assert contract.changes.get().identifier == "C1-A1"
    assert contract.cashdepositcollateral_collaterals.get().amount == 100


def test_payment_schedule_saves_draft_installments(admin_client):
    agreement = LandUseAgreement.objects.create(identifier="MA101-5")
    party = AgreementParty.objects.create(agreement=agreement)
    contract = Contract.objects.create(agreement=agreement)
    response = admin_client.put(
        reverse("v1:landuse:agreement-payment-schedules", args=(agreement.pk,)),
        [
            {
                "recipient_party": party.pk,
                "contract": contract.pk,
                "installments": [
                    {
                        "installment_sequence_number": 1,
                        "installment_count_total": 1,
                        "due_date": "2026-12-01",
                        "items": [
                            {"item_type": "LAND_USE_COMPENSATION", "amount": "100.00"}
                        ],
                    },
                ],
            }
        ],
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK
    schedule = agreement.payment_schedules.get()
    assert schedule.status == "DRAFT"
    assert schedule.installments.get().items.get().amount == 100


def test_compensation_document_saves_amounts_and_sites_together(admin_client):
    agreement = LandUseAgreement.objects.create(identifier="MA101-6")
    response = admin_client.put(
        reverse("v1:landuse:agreement-compensation-document", args=(agreement.pk,)),
        {
            "compensation": {"monetary_compensation": "100.00"},
            "sites": [{"identifier": "91-1-1-1"}],
        },
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK, response.json()
    assert agreement.compensation.monetary_compensation == 100
    assert agreement.compensation_sites.get().identifier == "91-1-1-1"


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
