import json

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from leasing.enums import LeaseState
from leasing.serializers import LeaseCreateUpdateSerializer, TenantCreateUpdateSerializer


@pytest.mark.django_db
def test_create_lease(contact_factory):
    contact_factory(name="Test contact")

    data = """{
    "application": null,
    "preparer": null,
    "real_property_units": [
        {
            "identification_number": "123-456-789-123",
            "name": null,
            "area": 2000,
            "registry_date": "1999-01-20",
            "detailed_plans": [
                {
                    "identification_number": "DP-12345",
                    "description": "Detailed plan 1",
                    "date": "2017-05-22",
                    "state": "proposal"
                }
            ],
            "plot_divisions": [
                {
                    "identification_number": "PD-1",
                    "description": "Plot division 1",
                    "date": null,
                    "state": "draft"
                },
                {
                    "identification_number": "PD-2",
                    "description": "Plot division 2",
                    "date": "2016-01-01",
                    "state": "final_decision"
                }
            ]
        },
        {
            "identification_number": "123-456-789-456",
            "name": null,
            "area": 2001,
            "registry_date": "2000-01-20",
            "addresses": [
                {
                    "address": "Address 1"
                },
                {
                    "address": "Address 2"
                }
            ]
        }
    ],
    "tenants": [
        {
            "contact": 1,
            "billing_contact": 1,
            "share_numerator": 1,
            "share_denominator": 1
        }
    ],
    "building_footprints": [
        {
            "use": "use1",
            "area": "11"
        },
        {
            "use": "use2",
            "area": "12"
        }
    ],
    "is_reservation": false,
    "state": "draft",
    "identifier": null,
    "reasons": "Reason",
    "detailed_plan": null,
    "detailed_plan_area": null
}"""

    serializer = LeaseCreateUpdateSerializer(data=json.loads(data))

    assert serializer.is_valid(raise_exception=True)
    instance = serializer.save()

    assert instance.id
    assert instance.state == LeaseState.DRAFT

    assert len(instance.real_property_units.all()) == 2

    rpu = instance.real_property_units.filter(identification_number="123-456-789-123").first()
    assert len(rpu.addresses.all()) == 0
    assert len(rpu.detailed_plans.all()) == 1
    assert len(rpu.plot_divisions.all()) == 2

    rpu = instance.real_property_units.filter(identification_number="123-456-789-456").first()
    assert len(rpu.addresses.all()) == 2
    assert len(rpu.detailed_plans.all()) == 0
    assert len(rpu.plot_divisions.all()) == 0

    assert len(instance.building_footprints.all()) == 2
    assert len(instance.tenants.all()) == 1
    assert instance.tenants.all()[0].contact.name == "Test contact"
    assert instance.tenants.all()[0].share_numerator == 1
    assert instance.tenants.all()[0].share_denominator == 1


@pytest.mark.django_db
def test_create_tenant(lease_factory, contact_factory):
    lease1 = lease_factory(state=LeaseState.DRAFT)
    contact_factory(id=1, name="Test contact")

    data = """{
        "contact": 1,
        "billing_contact": 1,
        "share_numerator": 1,
        "share_denominator": 1
    }"""

    serializer = TenantCreateUpdateSerializer(data=json.loads(data))

    assert serializer.is_valid(raise_exception=True)

    instance = serializer.save(lease=lease1)

    assert instance.id


@pytest.mark.django_db
def test_create_lease_without_identifier(user_factory, application_factory):
    user1 = user_factory(username='user1', password='user1', email='user1@example.com', is_superuser=True)

    data = {
        "preparer": user1.id,
        "state": "draft"
    }

    api_client = APIClient()
    api_client.credentials(HTTP_AUTHORIZATION='Token ' + user1.username)

    url = reverse('v1:lease-list')

    response = api_client.post(url, data=data)

    assert response.status_code == 201, '%s %s' % (response.status_code, response.data)
    assert response.data['identifier'] == ''


@pytest.mark.django_db
def test_create_lease_with_identifier(user_factory, application_factory):
    user1 = user_factory(username='user1', password='user1', email='user1@example.com', is_superuser=True)

    data = {
        "preparer": user1.id,
        "identifier_type": "A2",
        "identifier_municipality": "1",
        "identifier_district": "05",
        "state": "draft"
    }

    api_client = APIClient()
    api_client.credentials(HTTP_AUTHORIZATION='Token ' + user1.username)

    url = reverse('v1:lease-list')

    response = api_client.post(url, data=data)

    assert response.status_code == 201, '%s %s' % (response.status_code, response.data)
    assert response.data['identifier'] == 'A2105-1'
