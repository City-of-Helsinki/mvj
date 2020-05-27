import json

import pytest
from django.core.serializers.json import DjangoJSONEncoder
from django.urls import reverse

from leasing.models import Lease


@pytest.mark.django_db
def test_patch_lease_intended_use_note(django_db_setup, admin_client, lease_test_data):
    lease = lease_test_data["lease"]

    data = {"intended_use_note": "Updated note"}

    url = reverse("lease-detail", kwargs={"pk": lease.id})
    response = admin_client.patch(
        url,
        data=json.dumps(data, cls=DjangoJSONEncoder),
        content_type="application/json",
    )

    assert response.status_code == 200, "%s %s" % (response.status_code, response.data)

    lease = Lease.objects.get(pk=response.data["id"])

    assert lease.intended_use_note == "Updated note"


@pytest.mark.django_db
def test_remove_tenant(
    django_db_setup, admin_client, lease_test_data, assert_count_equal
):
    lease = lease_test_data["lease"]
    tenants = lease_test_data["tenants"]

    assert lease.tenants.count() == 2

    assert_count_equal(list(lease.tenants.all()), tenants)

    data = {
        "tenants": [
            {
                "id": tenants[0].id,
                "share_numerator": tenants[0].share_numerator,
                "share_denominator": tenants[0].share_denominator,
            }
        ]
    }

    url = reverse("lease-detail", kwargs={"pk": lease.id})
    response = admin_client.patch(
        url,
        data=json.dumps(data, cls=DjangoJSONEncoder),
        content_type="application/json",
    )

    assert response.status_code == 200, "%s %s" % (response.status_code, response.data)

    lease = Lease.objects.get(pk=response.data["id"])

    assert lease.tenants.count() == 1


@pytest.mark.django_db
def test_lease_area_addresses(
    django_db_setup, admin_client, lease_test_data, assert_count_equal
):
    lease = lease_test_data["lease"]
    lease_area = lease.lease_areas.first()

    data = {
        "lease_areas": [
            {
                "id": lease_area.id,
                "type": lease_area.type.value,
                "identifier": lease_area.identifier,
                "area": lease_area.area,
                "section_area": lease_area.section_area,
                "location": lease_area.location.value,
                "addresses": [
                    {"address": "Katu 1", "postal_code": "00190", "city": "Helsinki"},
                    {"address": "Katu 2", "postal_code": "00190", "city": "Helsinki"},
                ],
            }
        ]
    }

    url = reverse("lease-detail", kwargs={"pk": lease.id})
    response = admin_client.patch(
        url,
        data=json.dumps(data, cls=DjangoJSONEncoder),
        content_type="application/json",
    )

    assert response.status_code == 200, "%s %s" % (response.status_code, response.data)

    lease = Lease.objects.get(pk=response.data["id"])

    assert lease.lease_areas.count() == 1
    assert lease.lease_areas.first().addresses.count() == 2

    data = {
        "lease_areas": [
            {
                "id": lease_area.id,
                "type": lease_area.type.value,
                "identifier": lease_area.identifier,
                "area": lease_area.area,
                "section_area": lease_area.section_area,
                "location": lease_area.location.value,
                "addresses": None,
            }
        ]
    }

    response = admin_client.patch(
        url,
        data=json.dumps(data, cls=DjangoJSONEncoder),
        content_type="application/json",
    )

    assert response.status_code == 200, "%s %s" % (response.status_code, response.data)

    lease = Lease.objects.get(pk=response.data["id"])

    assert lease.lease_areas.count() == 1
    assert lease.lease_areas.first().addresses.count() == 0


@pytest.mark.django_db
def test_patch_lease_is_invoicing_enabled_not_possible(
    django_db_setup, admin_client, lease_test_data
):
    lease = lease_test_data["lease"]

    assert lease.is_invoicing_enabled is False

    data = {"is_invoicing_enabled": True}

    url = reverse("lease-detail", kwargs={"pk": lease.id})
    response = admin_client.patch(
        url,
        data=json.dumps(data, cls=DjangoJSONEncoder),
        content_type="application/json",
    )

    assert response.status_code == 200, "%s %s" % (response.status_code, response.data)

    lease = Lease.objects.get(pk=response.data["id"])

    assert lease.is_invoicing_enabled is False


@pytest.mark.django_db
def test_patch_lease_is_rent_info_complete_not_possible(
    django_db_setup, admin_client, lease_test_data
):
    lease = lease_test_data["lease"]

    assert lease.is_rent_info_complete is False

    data = {"is_rent_info_complete": True}

    url = reverse("lease-detail", kwargs={"pk": lease.id})
    response = admin_client.patch(
        url,
        data=json.dumps(data, cls=DjangoJSONEncoder),
        content_type="application/json",
    )

    assert response.status_code == 200, "%s %s" % (response.status_code, response.data)

    lease = Lease.objects.get(pk=response.data["id"])

    assert lease.is_rent_info_complete is False


def test_patch_lease_basis_of_rents(
    django_db_setup, admin_client, contact_factory, lease_test_data
):
    lease = lease_test_data["lease"]
    data = {
        "basis_of_rents": [{"intended_use": 1, "area": "101.00", "area_unit": "m2"}]
    }

    url = reverse("lease-detail", kwargs={"pk": lease.id})

    response = admin_client.patch(
        url,
        data=json.dumps(data, cls=DjangoJSONEncoder),
        content_type="application/json",
    )

    assert response.status_code == 200, "%s %s" % (response.status_code, response.data)


def test_patch_lease_basis_of_rents_without_intended_use(
    django_db_setup, admin_client, contact_factory, lease_test_data
):
    lease = lease_test_data["lease"]
    data = {"basis_of_rents": [{"area": "101.00", "area_unit": "m2"}]}

    url = reverse("lease-detail", kwargs={"pk": lease.id})

    response = admin_client.patch(
        url,
        data=json.dumps(data, cls=DjangoJSONEncoder),
        content_type="application/json",
    )

    assert response.status_code == 400, "%s %s" % (response.status_code, response.data)


def test_patch_lease_basis_of_rents_predefined_area_unit(
    django_db_setup, admin_client, contact_factory, lease_test_data
):
    lease = lease_test_data["lease"]
    data = {
        "basis_of_rents": [{"intended_use": 1, "area": "100.00", "area_unit": "m2"}]
    }

    url = reverse("lease-detail", kwargs={"pk": lease.id})

    response = admin_client.patch(
        url,
        data=json.dumps(data, cls=DjangoJSONEncoder),
        content_type="application/json",
    )

    data["basis_of_rents"] = [
        {
            "id": response.data["basis_of_rents"][0]["id"],
            "intended_use": 1,
            "area": "102.00",
        }
    ]
    response = admin_client.patch(
        url,
        data=json.dumps(data, cls=DjangoJSONEncoder),
        content_type="application/json",
    )

    assert response.status_code == 400, "%s %s" % (response.status_code, response.data)
