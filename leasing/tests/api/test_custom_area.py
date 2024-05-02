import json

import pytest
from django.core.serializers.json import DjangoJSONEncoder
from rest_framework.reverse import reverse

from leasing.models.land_area import CustomDetailedPlan, UsageDistribution
from leasing.serializers.land_area import LeaseAreaSerializer


@pytest.mark.django_db
def test_create_lease_with_custom_detailed_plan(
    django_db_setup, admin_client, custom_area_in_lease
):
    url = reverse("v1:lease-list")

    response = admin_client.post(
        url,
        data=json.dumps(custom_area_in_lease, cls=DjangoJSONEncoder),
        content_type="application/json",
    )

    assert response.status_code == 201

    assert CustomDetailedPlan.objects.count() == 1
    assert UsageDistribution.objects.count() == 1
    assert CustomDetailedPlan.objects.filter(identifier="54321").count() == 1


@pytest.mark.django_db
def test_change_custom_detailed_plan(django_db_setup, admin_client, lease_test_data):
    lease = lease_test_data["lease"]
    lease_area = lease_test_data["lease_area"]

    CustomDetailedPlan.objects.create(
        identifier="56789",
        lease_area=lease_area,
        address="Testaddress 1",
        area=10,
        rent_build_permission=0,
        intended_use_id=1,
    )

    lease_area_serializer = LeaseAreaSerializer(instance=lease_area)
    lease_area_data = lease_area_serializer.data

    lease_area_data["custom_detailed_plan"]["rent_build_permission"] = 4000

    data = {"lease_areas": [lease_area_data]}

    url = reverse("v1:lease-detail", kwargs={"pk": lease.id})
    response = admin_client.patch(
        url,
        data=json.dumps(data, cls=DjangoJSONEncoder),
        content_type="application/json",
    )
    assert response.status_code == 200, "{} {}".format(
        response.status_code, response.content
    )

    # Need to refresh from db to make the OneToOne field update
    lease_area.refresh_from_db()

    assert CustomDetailedPlan.objects.count() == 1
    assert lease_area.custom_detailed_plan.rent_build_permission == 4000


@pytest.mark.django_db
def test_add_custom_detailed_plan(django_db_setup, admin_client, lease_test_data):
    lease = lease_test_data["lease"]
    lease_area = lease_test_data["lease_area"]

    lease_area_serializer = LeaseAreaSerializer(instance=lease_area)
    lease_area_data = lease_area_serializer.data
    lease_area_data["custom_detailed_plan"] = {
        "identifier": "12345",
        "area": 10,
        "rent_build_permission": 0,
        "address": "Testaddress 1",
        "section_area": 0,
        "intended_use": 1,
        "usage_distributions": [
            {"distribution": 3, "build_permission": "5 m2", "note": "sito tontti"}
        ],
    }

    data = {"lease_areas": [lease_area_data]}

    url = reverse("v1:lease-detail", kwargs={"pk": lease.id})
    response = admin_client.patch(
        url,
        data=json.dumps(data, cls=DjangoJSONEncoder),
        content_type="application/json",
    )
    assert response.status_code == 200, "{} {}".format(
        response.status_code, response.content
    )

    # Need to refresh from db to make the OneToOne field update
    lease_area.refresh_from_db()

    assert hasattr(lease_area, "custom_detailed_plan")


@pytest.mark.django_db
def test_remove_custom_detailed_plan(django_db_setup, admin_client, lease_test_data):
    lease = lease_test_data["lease"]
    lease_area = lease_test_data["lease_area"]

    CustomDetailedPlan.objects.create(
        identifier="56789",
        lease_area=lease_area,
        area=10,
        rent_build_permission=0,
        intended_use_id=1,
    )

    lease_area_serializer = LeaseAreaSerializer(instance=lease_area)
    lease_area_data = lease_area_serializer.data
    lease_area_data["custom_detailed_plan"] = None

    data = {"lease_areas": [lease_area_data]}

    url = reverse("v1:lease-detail", kwargs={"pk": lease.id})
    response = admin_client.patch(
        url,
        data=json.dumps(data, cls=DjangoJSONEncoder),
        content_type="application/json",
    )
    assert response.status_code == 200, "{} {}".format(
        response.status_code, response.content
    )

    # Need to refresh from db to make the OneToOne field update
    lease_area.refresh_from_db()

    assert not hasattr(lease_area, "custom_detailed_plan")
