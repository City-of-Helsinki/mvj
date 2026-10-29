from importlib import import_module
from types import SimpleNamespace

import pytest
from django.apps import apps
from django.contrib.auth.models import Group, Permission
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
from landuse.models.compensation import LandPolicyProgram, LandUseCompensation
from landuse.models.party import AgreementParty, ContactPerson
from landuse.models.site import AgreementSite, SiteIntendedUse, SiteTenureType
from landuse.permissions import tab_permission
from utils.group_permissions import UG

pytestmark = [pytest.mark.django_db, pytest.mark.usefixtures("admin_client")]


@pytest.fixture(autouse=True)
def enable_landuse_api(settings):
    settings.FLAG_LANDUSE_API_ENABLED = True


@pytest.mark.parametrize(
    "role", [UG.VALMISTELIJA, UG.SOPIMUSVALMISTELIJA, UG.LASKUTTAJA, UG.PAAKAYTTAJA]
)
@pytest.mark.parametrize(
    "tab,editors",
    [
        (
            "parties",
            [UG.VALMISTELIJA, UG.SOPIMUSVALMISTELIJA, UG.LASKUTTAJA, UG.PAAKAYTTAJA],
        ),
        ("sites", [UG.VALMISTELIJA, UG.PAAKAYTTAJA]),
        ("compensation", [UG.VALMISTELIJA, UG.PAAKAYTTAJA]),
        ("decisions", [UG.VALMISTELIJA, UG.SOPIMUSVALMISTELIJA, UG.PAAKAYTTAJA]),
        ("contracts", [UG.VALMISTELIJA, UG.SOPIMUSVALMISTELIJA, UG.PAAKAYTTAJA]),
        ("payment-schedules", [UG.VALMISTELIJA, UG.PAAKAYTTAJA]),
        ("invoices", [UG.LASKUTTAJA, UG.PAAKAYTTAJA]),
    ],
)
def test_tab_role_matrix(client, tab_role_user, role, tab, editors, rf):
    user = tab_role_user(role)
    client.force_login(user)
    agreement = LandUseAgreement.objects.create(identifier="M-ROLE")
    url = reverse(f"v1:landuse:agreement-{tab}", args=(agreement.pk,))
    assert client.get(url).status_code == status.HTTP_200_OK
    if tab == "invoices":
        request = rf.put(url)
        request.user = user
        assert tab_permission("invoices")().has_permission(request, None) == (
            role in editors
        )
        return
    payload = {} if tab == "compensation" else []
    response = client.put(url, payload, content_type="application/json")
    assert response.status_code == (
        status.HTTP_200_OK if role in editors else status.HTTP_403_FORBIDDEN
    )
    if tab == "compensation" and role not in editors:
        assert not LandUseCompensation.objects.filter(agreement=agreement).exists()


def test_agreement_permission_does_not_authorize_tab(client, user_factory):
    user = user_factory(is_superuser=False)
    user.user_permissions.set(
        Permission.objects.filter(
            content_type__app_label="landuse",
            codename__in=["view_landuseagreement", "change_landuseagreement"],
        )
    )
    client.force_login(user)
    agreement = LandUseAgreement.objects.create(identifier="M-DENIED")
    party = AgreementParty.objects.create(agreement=agreement, name="Original")
    url = reverse("v1:landuse:agreement-parties", args=(agreement.pk,))
    assert client.get(url).status_code == status.HTTP_403_FORBIDDEN
    response = client.put(
        url, [{"id": party.pk, "name": "Changed"}], content_type="application/json"
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    party.refresh_from_db()
    assert party.name == "Original"


def test_tab_permission_does_not_require_agreement_permission(client, user_factory):
    user = user_factory(is_superuser=False)
    user.user_permissions.set(
        Permission.objects.filter(
            content_type__app_label="landuse",
            codename__in=["view_tab_parties", "change_tab_parties"],
        )
    )
    client.force_login(user)
    agreement = LandUseAgreement.objects.create(identifier="M-INDEPENDENT")
    url = reverse("v1:landuse:agreement-parties", args=(agreement.pk,))
    assert client.get(url).status_code == status.HTTP_200_OK
    assert (
        client.put(url, [{"name": "New"}], content_type="application/json").status_code
        == status.HTTP_200_OK
    )
    assert (
        client.get(
            reverse("v1:landuse:agreement-detail", args=(agreement.pk,))
        ).status_code
        == status.HTTP_403_FORBIDDEN
    )


@pytest.mark.parametrize(
    "permissions", [[], ["change_tab_compensation"], ["change_tab_sites"]]
)
def test_combined_compensation_write_requires_both_tabs(
    client, user_factory, permissions
):
    user = user_factory(is_superuser=False)
    user.user_permissions.set(
        Permission.objects.filter(
            content_type__app_label="landuse", codename__in=permissions
        )
    )
    client.force_login(user)
    agreement = LandUseAgreement.objects.create(identifier="M-COMBINED-DENIED")
    response = client.put(
        reverse("v1:landuse:agreement-compensation-with-sites", args=(agreement.pk,)),
        {"compensation": {}, "sites": []},
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert not LandUseCompensation.objects.filter(agreement=agreement).exists()


@pytest.mark.parametrize(
    "method,action,permission,expected",
    [
        ("get", "list", "view", status.HTTP_200_OK),
        ("get", "detail", "view", status.HTTP_200_OK),
        ("get", "overview", "view", status.HTTP_200_OK),
        ("post", "list", "add", status.HTTP_201_CREATED),
        ("put", "detail", "change", status.HTTP_200_OK),
        ("patch", "detail", "change", status.HTTP_200_OK),
        ("delete", "detail", "delete", status.HTTP_204_NO_CONTENT),
    ],
)
def test_agreement_crud_keeps_standard_permissions(
    client, user_factory, method, action, permission, expected
):
    user = user_factory(is_superuser=False)
    client.force_login(user)
    district = District.objects.create(name="District", identifier="07")
    agreement = LandUseAgreement.objects.create(
        identifier="M-STANDARD", district=district
    )
    url = reverse(
        f"v1:landuse:agreement-{action}",
        args=() if action == "list" else (agreement.pk,),
    )
    payload = {"identifier": "M-STANDARD", "district": district.pk}
    request = getattr(client, method)
    assert (
        request(url, payload, content_type="application/json").status_code
        == status.HTTP_403_FORBIDDEN
    )
    user.user_permissions.add(
        Permission.objects.get(
            content_type__app_label="landuse", codename=f"{permission}_landuseagreement"
        )
    )
    assert (
        request(url, payload, content_type="application/json").status_code == expected
    )


@pytest.mark.parametrize(
    "tab",
    [
        "parties",
        "sites",
        "compensation",
        "decisions",
        "contracts",
        "payment-schedules",
        "invoices",
    ],
)
def test_tab_requires_authentication(client, tab):
    client.logout()
    agreement = LandUseAgreement.objects.create(identifier="M-ANONYMOUS")
    url = reverse(f"v1:landuse:agreement-{tab}", args=(agreement.pk,))
    assert client.get(url).status_code == status.HTTP_401_UNAUTHORIZED


def test_stale_assignment_cleanup_preserves_permission_rows_and_other_groups():
    migration = import_module("landuse.migrations.0011_agreement_tab_permissions")
    managed, _ = Group.objects.get_or_create(
        pk=UG.VALMISTELIJA, defaults={"name": "Managed"}
    )
    unmanaged = Group.objects.create(pk=9999, name="Unmanaged")
    stale = Permission.objects.get(
        content_type__app_label="landuse", codename="change_agreementparty"
    )
    retained = Permission.objects.get(
        content_type__app_label="landuse", codename="view_landuseagreement"
    )
    managed.permissions.add(stale, retained)
    unmanaged.permissions.add(stale)
    migration.remove_obsolete_group_assignments(
        apps, SimpleNamespace(connection=SimpleNamespace(alias="default"))
    )
    assert not managed.permissions.filter(pk=stale.pk).exists()
    assert managed.permissions.filter(pk=retained.pk).exists()
    assert unmanaged.permissions.filter(pk=stale.pk).exists()
    assert Permission.objects.filter(pk=stale.pk).exists()


@pytest.mark.parametrize(
    "language,country", [("fi", "FI"), ("sv", "SE"), ("en", "DE"), ("", "")]
)
def test_party_and_alternate_recipient_codes_round_trip(
    admin_client, language, country
):
    agreement = LandUseAgreement.objects.create(identifier="M-CODES")
    url = reverse("v1:landuse:agreement-parties", args=(agreement.pk,))
    response = admin_client.put(
        url,
        [
            {
                "party_type": "COMPANY",
                "language": language,
                "country": country,
                "invoice_recipient": {
                    "party_type": "PERSON",
                    "language": language,
                    "country": country,
                },
            }
        ],
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK
    saved = response.json()[0]
    assert saved["language"] == language
    assert saved["country"] == country
    assert saved["invoice_recipient"]["language"] == language
    assert saved["invoice_recipient"]["country"] == country
    response = admin_client.put(url, response.json(), content_type="application/json")
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.parametrize("field,value", [("language", "suomi"), ("country", "Suomi")])
@pytest.mark.parametrize("alternate", [False, True])
def test_party_codes_reject_labels(admin_client, field, value, alternate):
    agreement = LandUseAgreement.objects.create(identifier="M-INVALID-CODES")
    details = {field: value}
    payload = {"invoice_recipient": details} if alternate else details
    response = admin_client.put(
        reverse("v1:landuse:agreement-parties", args=(agreement.pk,)),
        [payload],
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert not agreement.parties.exists()


def test_agreement_list_includes_searchable_projections_and_status_label(
    admin_client,
):
    plan = DetailedPlan.objects.create(plan_number="12345")
    agreement = LandUseAgreement.objects.create(
        identifier="M-LIST",
        detailed_plan=plan,
        is_promotion_area=True,
        status="IN_PROGRESS",
    )
    AgreementParty.objects.create(agreement=agreement, name="List party")
    AgreementSite.objects.create(agreement=agreement, identifier="List site")

    response = admin_client.get(reverse("v1:landuse:agreement-list"))

    assert response.status_code == status.HTTP_200_OK
    listed = response.json()["results"][0]
    assert listed["party"] == "List party"
    assert listed["zoning_plan_number"] == "12345"
    assert listed["site"] == "List site"
    assert listed["is_promotion_area"] is True
    assert listed["status"] == "IN_PROGRESS"
    assert listed["status_label"] == "Vireillä"


def test_agreement_creation_uses_official_district_identifier(admin_client):
    district = District.objects.create(name="District", identifier="07")
    LandUseAgreement.objects.create(identifier="MA107-2", district=district)

    response = admin_client.post(
        reverse("v1:landuse:agreement-list"),
        {"district": district.pk, "identifier": "MA199-999"},
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["identifier"] == "MA107-3"


def test_referenced_decision_removal_is_a_conflict_and_rolls_back(admin_client):
    from landuse.models.contract import Contract
    from landuse.models.decision import Decision

    agreement = LandUseAgreement.objects.create(identifier="M-CONFLICT")
    retained = Decision.objects.create(agreement=agreement, title="Original")
    removed = Decision.objects.create(agreement=agreement)
    contract = Contract.objects.create(agreement=agreement, decision=removed)
    response = admin_client.put(
        reverse("v1:landuse:agreement-decisions", args=(agreement.pk,)),
        [{"id": retained.pk, "title": "Changed"}],
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json()["code"] == "referenced_decisions"
    retained.refresh_from_db()
    assert retained.title == "Original"
    assert Decision.objects.filter(pk=removed.pk).exists()
    assert Contract.objects.filter(pk=contract.pk).exists()


def test_referenced_party_removal_is_a_conflict(admin_client):
    from landuse.models.contract import Contract
    from landuse.models.payment_schedule import PaymentSchedule

    agreement = LandUseAgreement.objects.create(identifier="M-CONFLICT")
    party = AgreementParty.objects.create(agreement=agreement, name="Retained")
    contract = Contract.objects.create(agreement=agreement)
    PaymentSchedule.objects.create(
        agreement=agreement, recipient_party=party, contract=contract
    )
    response = admin_client.put(
        reverse("v1:landuse:agreement-parties", args=(agreement.pk,)),
        [],
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json()["code"] == "referenced_parties"
    assert AgreementParty.objects.filter(pk=party.pk).exists()


def test_invoice_party_removal_rolls_back_retained_party_edits(admin_client):
    from landuse.models.invoice import Invoice

    agreement = LandUseAgreement.objects.create(identifier="M-INVOICE-CONFLICT")
    retained = AgreementParty.objects.create(agreement=agreement, name="Original")
    removed = AgreementParty.objects.create(agreement=agreement)
    Invoice.objects.create(
        agreement=agreement,
        recipient_party=removed,
        invoice_identifier="INV-CONFLICT",
        installment_sequence_number=1,
        installment_count_total=1,
    )
    response = admin_client.put(
        reverse("v1:landuse:agreement-parties", args=(agreement.pk,)),
        [{"id": retained.pk, "name": "Changed"}],
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_409_CONFLICT
    retained.refresh_from_db()
    assert retained.name == "Original"
    assert AgreementParty.objects.filter(pk=removed.pk).exists()


def test_contract_change_decision_removal_is_blocked(admin_client):
    from landuse.models.contract import Contract, ContractChange
    from landuse.models.decision import Decision

    agreement = LandUseAgreement.objects.create(identifier="M-CHANGE-CONFLICT")
    decision = Decision.objects.create(agreement=agreement)
    contract = Contract.objects.create(agreement=agreement)
    change = ContractChange.objects.create(contract=contract, decision=decision)
    response = admin_client.put(
        reverse("v1:landuse:agreement-decisions", args=(agreement.pk,)),
        [],
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_409_CONFLICT
    assert ContractChange.objects.filter(pk=change.pk).exists()


def test_contracts_replace_nested_contract_changes_and_collaterals(admin_client):
    from landuse.models.contract import OtherCollateral
    from landuse.models.decision import Decision

    agreement = LandUseAgreement.objects.create(identifier="M-CONTRACT-WRITE")
    party = AgreementParty.objects.create(agreement=agreement, name="Party")
    decision = Decision.objects.create(agreement=agreement, title="Decision")
    url = reverse("v1:landuse:agreement-contracts", args=(agreement.pk,))
    payload = [
        {
            "identifier": "C-1",
            "title": "Contract",
            "contract_type": "OTHER",
            "decision": decision.pk,
            "changes": [{"identifier": "C-1A", "decision": decision.pk}],
            "other_collaterals": [
                {
                    "parties": [party.pk],
                    "guarantor_name": "Guarantor",
                }
            ],
        }
    ]

    response = admin_client.put(url, payload, content_type="application/json")

    assert response.status_code == status.HTTP_200_OK
    saved = response.json()[0]
    collateral = saved["other_collaterals"][0]
    assert saved["changes"][0]["identifier"] == "C-1A"
    assert collateral["parties"] == [party.pk]
    response = admin_client.put(
        url,
        [
            {
                **payload[0],
                "id": saved["id"],
                "title": "Updated contract",
                "changes": [{"id": saved["changes"][0]["id"], "identifier": "C-1B"}],
                "other_collaterals": [{"id": collateral["id"]}],
            }
        ],
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()[0]["title"] == "Updated contract"
    assert OtherCollateral.objects.get(pk=collateral["id"]).contract_id == saved["id"]


def test_payment_schedules_replace_nested_rows_and_reject_foreign_contract(
    admin_client,
):
    from landuse.models.contract import Contract

    agreement = LandUseAgreement.objects.create(identifier="M-SCHEDULE-WRITE")
    party = AgreementParty.objects.create(agreement=agreement, name="Recipient")
    contract = Contract.objects.create(agreement=agreement)
    foreign_agreement = LandUseAgreement.objects.create(identifier="M-FOREIGN")
    foreign_contract = Contract.objects.create(agreement=foreign_agreement)
    url = reverse("v1:landuse:agreement-payment-schedules", args=(agreement.pk,))
    payload = [
        {
            "recipient_party": party.pk,
            "contract": contract.pk,
            "installments": [
                {
                    "installment_sequence_number": 1,
                    "installment_count_total": 1,
                    "items": [
                        {
                            "item_type": "LAND_USE_COMPENSATION",
                            "description": "Compensation",
                            "amount": "10.00",
                        }
                    ],
                }
            ],
        }
    ]

    response = admin_client.put(url, payload, content_type="application/json")

    assert response.status_code == status.HTTP_200_OK
    saved = response.json()[0]
    assert saved["installments"][0]["items"][0]["amount"] == "10.00"
    response = admin_client.put(
        url,
        [{**payload[0], "contract": foreign_contract.pk}],
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert agreement.payment_schedules.count() == 1


def test_unchanged_contact_persons_keep_their_primary_key(admin_client):
    agreement = LandUseAgreement.objects.create(identifier="M-KEEP-CONTACTS")
    url = reverse("v1:landuse:agreement-parties", args=(agreement.pk,))
    payload = [
        {
            "party_type": "COMPANY",
            "name": "Party",
            "contact_persons": [{"name": "Alice", "phone": "1", "email": "a@x.fi"}],
        }
    ]
    first = admin_client.put(url, payload, content_type="application/json").json()
    contact_pk = ContactPerson.objects.get(agreement_party_id=first[0]["id"]).pk

    response = admin_client.put(url, first, content_type="application/json")

    assert response.status_code == status.HTTP_200_OK
    assert ContactPerson.objects.get(agreement_party_id=first[0]["id"]).pk == contact_pk


def test_changed_contact_person_keeps_its_id(admin_client):
    agreement = LandUseAgreement.objects.create(identifier="M-CHANGE-CONTACTS")
    url = reverse("v1:landuse:agreement-parties", args=(agreement.pk,))
    first = admin_client.put(
        url,
        [
            {
                "party_type": "COMPANY",
                "name": "Party",
                "contact_persons": [{"name": "Alice"}],
            }
        ],
        content_type="application/json",
    ).json()
    contact_pk = first[0]["contact_persons"][0]["id"]
    first[0]["contact_persons"][0]["name"] = "Alicia"

    response = admin_client.put(url, first, content_type="application/json")

    assert response.status_code == status.HTTP_200_OK
    contact = ContactPerson.objects.get(agreement_party_id=first[0]["id"])
    assert contact.pk == contact_pk
    assert contact.name == "Alicia"


def _put_contract(admin_client, agreement, contract, collaterals_by_key):
    return admin_client.put(
        reverse("v1:landuse:agreement-contracts", args=(agreement.pk,)),
        [{"id": contract.pk, "identifier": "C-COLL", **collaterals_by_key}],
        content_type="application/json",
    )


def test_legacy_flat_collaterals_key_is_rejected(admin_client):
    from landuse.models.contract import Contract, OtherCollateral

    agreement = LandUseAgreement.objects.create(identifier="M-COLL-LEGACY")
    contract = Contract.objects.create(agreement=agreement)
    collateral = OtherCollateral.objects.create(
        contract=contract, guarantee_type="OTHER"
    )

    response = _put_contract(
        admin_client,
        agreement,
        contract,
        {"collaterals": [{"guarantee_type": "OTHER"}]},
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert OtherCollateral.objects.filter(pk=collateral.pk).exists()


def test_collateral_id_from_another_contract_is_rejected(admin_client):
    from landuse.models.contract import Contract, OtherCollateral

    agreement = LandUseAgreement.objects.create(identifier="M-COLL-FOREIGN")
    contract = Contract.objects.create(agreement=agreement)
    other_contract = Contract.objects.create(agreement=agreement)
    foreign = OtherCollateral.objects.create(
        contract=other_contract, guarantee_type="OTHER"
    )

    response = _put_contract(
        admin_client,
        agreement,
        contract,
        {"other_collaterals": [{"id": foreign.pk}]},
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert OtherCollateral.objects.filter(pk=foreign.pk).exists()


def test_invalid_collateral_party_rolls_back_whole_contract_write(admin_client):
    from landuse.models.contract import Contract, OtherCollateral

    agreement = LandUseAgreement.objects.create(identifier="M-COLL-ROLLBACK")
    contract = Contract.objects.create(agreement=agreement)
    kept = OtherCollateral.objects.create(
        contract=contract, guarantee_type="OTHER", guarantor_name="Original"
    )
    foreign_party = AgreementParty.objects.create(
        agreement=LandUseAgreement.objects.create(identifier="M-COLL-FOREIGN-PARTY"),
        name="Foreign",
    )

    response = _put_contract(
        admin_client,
        agreement,
        contract,
        {
            "other_collaterals": [
                {"id": kept.pk, "guarantor_name": "Changed"},
                {"parties": [foreign_party.pk]},
            ]
        },
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    kept.refresh_from_db()
    assert kept.guarantor_name == "Original"
    assert OtherCollateral.objects.filter(contract=contract).count() == 1


def test_property_identifiers_rejected_for_facility_target(admin_client):
    from landuse.models.contract import Contract, MortgageDeedCollateral

    agreement = LandUseAgreement.objects.create(identifier="M-COLL-FACILITY")
    contract = Contract.objects.create(agreement=agreement)

    response = _put_contract(
        admin_client,
        agreement,
        contract,
        {
            "mortgage_deed_collaterals": [
                {
                    "target": MortgageDeedCollateral.CollateralTarget.FACILITY,
                    "property_identifiers": ["123-456"],
                }
            ]
        },
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert not MortgageDeedCollateral.objects.filter(contract=contract).exists()


def test_fields_not_applicable_to_collateral_type_are_rejected(admin_client):
    from landuse.models.contract import Contract

    agreement = LandUseAgreement.objects.create(identifier="M-COLL-FIELDS")
    contract = Contract.objects.create(agreement=agreement)

    response = _put_contract(
        admin_client,
        agreement,
        contract,
        {"cash_deposit_collaterals": [{"document_category": "X"}]},
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "document_category" in response.json()["0"]["cash_deposit_collaterals"]["0"]


@pytest.mark.parametrize("resource", ["parties", "decisions"])
def test_unreferenced_rows_can_be_removed(admin_client, resource):
    from landuse.models.decision import Decision

    agreement = LandUseAgreement.objects.create(identifier="M-REMOVE")
    model = AgreementParty if resource == "parties" else Decision
    model.objects.create(agreement=agreement)
    response = admin_client.put(
        reverse(f"v1:landuse:agreement-{resource}", args=(agreement.pk,)),
        [],
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK
    assert not model.objects.filter(agreement=agreement).exists()


@pytest.mark.parametrize("designation", ["SR1", "SR2", "SR3", None, ""])
def test_site_preservation_selection_and_clearing(admin_client, designation):
    agreement = LandUseAgreement.objects.create(identifier="M-PRESERVATION")
    tenure_type = SiteTenureType.objects.create(name="Rental")
    url = reverse("v1:landuse:agreement-sites", args=(agreement.pk,))
    response = admin_client.put(
        url,
        [{"tenure_types": [tenure_type.pk], "preservation_designation": designation}],
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()[0]["preservation_designation"] == designation
    response = admin_client.put(
        url,
        [
            {
                "id": response.json()[0]["id"],
                "tenure_types": [tenure_type.pk],
                "preservation_designation": None,
            }
        ],
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()[0]["preservation_designation"] is None
    response = admin_client.put(
        url,
        [{"tenure_types": [tenure_type.pk], "preservation_designation": "-"}],
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


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


def test_agreement_updates_summary_relations(admin_client, django_user_model):
    agreement = LandUseAgreement.objects.create(identifier="M-2026-1")
    signatory = AuthorizedSignatory.objects.create(name="Signatory")
    preparer = django_user_model.objects.create(username="summary-preparer")
    AgreementAddress.objects.create(
        agreement=agreement, street_address="Old", postal_code="00100", city="Helsinki"
    )
    AgreementPreparer.objects.create(agreement=agreement, preparer=preparer)
    url = reverse("v1:landuse:agreement-detail", args=(agreement.pk,))

    response = admin_client.patch(
        url,
        {
            "authorized_signatory": signatory.pk,
            "addresses": [
                {"street_address": "New", "postal_code": "00200", "city": "Helsinki"}
            ],
            "preparers": [{"preparer": preparer.pk}],
        },
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_200_OK
    agreement.refresh_from_db()
    assert agreement.authorized_signatory_id == signatory.pk
    assert list(agreement.addresses.values_list("street_address", flat=True)) == ["New"]
    assert list(agreement.preparers.values_list("preparer_id", flat=True)) == [
        preparer.pk
    ]

    overview = admin_client.get(
        reverse("v1:landuse:agreement-overview", args=(agreement.pk,))
    ).json()
    assert overview["authorized_signatory"]["id"] == signatory.pk
    assert overview["addresses"][0]["street_address"] == "New"
    assert overview["preparers"][0]["preparer"] == preparer.pk

    response = admin_client.patch(
        url,
        {"addresses": [], "preparers": [{"preparer": 0}]},
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert agreement.addresses.count() == 1
    assert agreement.preparers.count() == 1

    response = admin_client.patch(
        url, {"status": "DRAFT"}, content_type="application/json"
    )
    assert response.status_code == status.HTTP_200_OK
    assert agreement.addresses.count() == 1
    assert agreement.preparers.count() == 1

    response = admin_client.patch(
        url,
        {"authorized_signatory": None, "addresses": [], "preparers": []},
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK
    agreement.refresh_from_db()
    assert agreement.authorized_signatory_id is None
    assert not agreement.addresses.exists()
    assert not agreement.preparers.exists()


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


@pytest.mark.parametrize(
    "payload",
    [
        {
            "compensation": {"monetary_compensation": "200.00"},
            "sites": [{"intended_use": 999999, "tenure_types": []}],
        },
        {
            "compensation": {"land_policy_program": 999999},
            "sites": [
                {
                    "identifier": "New site",
                    "intended_use": None,
                    "tenure_types": [],
                }
            ],
        },
    ],
)
def test_compensation_with_sites_rejects_partial_writes(admin_client, payload):
    agreement = LandUseAgreement.objects.create(identifier="M-ATOMIC")
    LandUseCompensation.objects.create(
        agreement=agreement, monetary_compensation="100.00"
    )
    AgreementSite.objects.create(agreement=agreement, identifier="Existing site")

    response = admin_client.put(
        reverse("v1:landuse:agreement-compensation-with-sites", args=(agreement.pk,)),
        payload,
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    agreement.refresh_from_db()
    assert agreement.compensation.monetary_compensation == 100
    assert list(agreement.compensation_sites.values_list("identifier", flat=True)) == [
        "Existing site"
    ]


def test_compensation_with_sites_saves_both_resources(admin_client):
    agreement = LandUseAgreement.objects.create(identifier="M-ATOMIC-SUCCESS")
    intended_use = SiteIntendedUse.objects.create(name="Residential")
    tenure_type = SiteTenureType.objects.create(name="Rental")

    response = admin_client.put(
        reverse("v1:landuse:agreement-compensation-with-sites", args=(agreement.pk,)),
        {
            "compensation": {"monetary_compensation": "200.00"},
            "sites": [
                {
                    "identifier": "New site",
                    "intended_use": intended_use.pk,
                    "tenure_types": [tenure_type.pk],
                }
            ],
        },
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_200_OK
    agreement.refresh_from_db()
    assert agreement.compensation.monetary_compensation == 200
    assert response.json()["sites"][0]["intended_use"]["id"] == intended_use.pk
    assert response.json()["sites"][0]["tenure_types"] == [
        {"id": tenure_type.pk, "name": "Rental"}
    ]
