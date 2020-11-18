import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_list_land_use_agreements(
    django_db_setup, admin_client, land_use_agreement_test_data
):

    url = reverse("landuseagreement-list")

    response = admin_client.get(url, content_type="application/json")
    assert response.status_code == 200, "%s %s" % (response.status_code, response.data)


@pytest.mark.django_db
def test_get_land_use_agreement(
    django_db_setup, admin_client, land_use_agreement_test_data
):
    url = reverse(
        "landuseagreement-detail", kwargs={"pk": land_use_agreement_test_data.id}
    )

    response = admin_client.get(url, content_type="application/json")
    assert response.status_code == 200, "%s %s" % (response.status_code, response.data)

    assert response.data.get("id") == land_use_agreement_test_data.id
    assert response.data.get("type") == land_use_agreement_test_data.type_id
    assert (
        response.data.get("preparer").get("username")
        == land_use_agreement_test_data.preparer.username
    )
    assert (
        response.data.get("land_use_contract_type")
        == land_use_agreement_test_data.land_use_contract_type.value
    )
    assert (
        response.data.get("plan_acceptor")
        == land_use_agreement_test_data.plan_acceptor.id
    )
    assert (
        response.data.get("estimated_completion_year")
        == land_use_agreement_test_data.estimated_completion_year
    )
    assert (
        response.data.get("estimated_introduction_year")
        == land_use_agreement_test_data.estimated_introduction_year
    )
    assert (
        response.data.get("project_area") == land_use_agreement_test_data.project_area
    )
    assert (
        response.data.get("plan_reference_number")
        == land_use_agreement_test_data.plan_reference_number
    )
    assert response.data.get("plan_number") == land_use_agreement_test_data.plan_number
    assert response.data.get(
        "plan_lawfulness_date"
    ) == land_use_agreement_test_data.plan_lawfulness_date.strftime("%Y-%m-%d")
    assert response.data.get("state") == land_use_agreement_test_data.state
    assert response.data.get("addresses")[0].get("address") == "Testikatu 1"
    assert response.data.get("contracts")[0].get("contract_number") == "A123"
    assert (
        response.data.get("conditions")[0].get("description")
        == "test_condition_description"
    )
    assert response.data.get("decisions")[0].get("reference_number") == "1234"
    response_litigants = response.data.get("litigants")
    assert len(response_litigants) == 2
    contact_set = response_litigants[0].get("landuseagreementlitigantcontact_set")
    assert "Litigant First" in contact_set[0].get("contact")["first_name"]


@pytest.mark.django_db
def test_update_land_use_agreement(
    django_db_setup, admin_client, land_use_agreement_test_data, user_factory,
):

    url = reverse(
        "landuseagreement-detail", kwargs={"pk": land_use_agreement_test_data.id}
    )
    user = user_factory(username="test_user_2")

    data = {
        "id": land_use_agreement_test_data.id,
        "type": land_use_agreement_test_data.type.id,
        "status": land_use_agreement_test_data.status.id,
        "definition": land_use_agreement_test_data.definition.id,
        "preparer": user.id,
        "estates": ["TEST"],
        "municipality": land_use_agreement_test_data.municipality.id,
        "district": land_use_agreement_test_data.district.id,
        "addresses": [
            {"address": "Testikatu 2", "postal_code": "00100", "city": "Helsinki"}
        ],
    }
    response = admin_client.put(url, data=data, content_type="application/json")
    assert response.status_code == 200, "%s %s" % (response.status_code, response.data)
    assert response.data.get("addresses")[0].get("address") == "Testikatu 2"


@pytest.mark.django_db
def test_create_land_use_agreement(
    django_db_setup, admin_client, land_use_agreement_test_data, user_factory,
):

    url = reverse("landuseagreement-list")
    user = user_factory(username="test_user_2")

    data = {
        "type": land_use_agreement_test_data.type.id,
        "status": land_use_agreement_test_data.status.id,
        "definition": land_use_agreement_test_data.definition.id,
        "preparer": user.id,
        "municipality": land_use_agreement_test_data.municipality.id,
        "district": land_use_agreement_test_data.district.id,
        "addresses": [
            {"address": "Testikatu 1", "postal_code": "00100", "city": "Helsinki"}
        ],
    }
    response = admin_client.post(url, data=data, content_type="application/json")
    assert response.status_code == 201, "%s %s" % (response.status_code, response.data)


@pytest.mark.django_db
def test_create_land_use_agreement_w_two_addresses(
    django_db_setup, admin_client, land_use_agreement_test_data, user_factory,
):

    url = reverse("landuseagreement-list")
    user = user_factory(username="test_user_2")

    data = {
        "type": land_use_agreement_test_data.type.id,
        "status": land_use_agreement_test_data.status.id,
        "definition": land_use_agreement_test_data.definition.id,
        "preparer": user.id,
        "municipality": land_use_agreement_test_data.municipality.id,
        "district": land_use_agreement_test_data.district.id,
        "addresses": [
            {
                "address": "Testikatu 1",
                "postal_code": "00100",
                "city": "Helsinki",
                "is_primary": True,
            },
            {
                "address": "Testikatu 666",
                "postal_code": "00100",
                "city": "Helsinki",
                "is_primary": False,
            },
        ],
    }
    response = admin_client.post(url, data=data, content_type="application/json")
    assert response.status_code == 201, "%s %s" % (response.status_code, response.data)
    assert len(response.data.get("addresses", [])) == 2
