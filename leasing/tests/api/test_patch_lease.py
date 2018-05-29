import json

import pytest
from django.core.serializers.json import DjangoJSONEncoder
from django.urls import reverse

from leasing.models import Lease


@pytest.mark.django_db
def test_patch_lease_intended_use_note(django_db_setup, admin_client, lease_test_data):
    lease = lease_test_data['lease']

    data = {
        "intended_use_note": "Updated note",
    }

    url = reverse('lease-detail', kwargs={'pk': lease.id})
    response = admin_client.patch(url, data=json.dumps(data, cls=DjangoJSONEncoder), content_type='application/json')

    assert response.status_code == 200, '%s %s' % (response.status_code, response.data)

    lease = Lease.objects.get(pk=response.data['id'])

    assert lease.intended_use_note == "Updated note"


@pytest.mark.django_db
def test_remove_tenant(django_db_setup, admin_client, lease_test_data, assert_count_equal):
    lease = lease_test_data['lease']
    tenants = lease_test_data['tenants']

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

    url = reverse('lease-detail', kwargs={'pk': lease.id})
    response = admin_client.patch(url, data=json.dumps(data, cls=DjangoJSONEncoder), content_type='application/json')

    assert response.status_code == 200, '%s %s' % (response.status_code, response.data)

    lease = Lease.objects.get(pk=response.data['id'])

    assert lease.tenants.count() == 1


@pytest.mark.django_db
def test_lease_area_addresses(django_db_setup, admin_client, lease_test_data, assert_count_equal):
    lease = lease_test_data['lease']
    lease_area = lease.lease_areas.first()

    data = {
        "lease_areas": [{
            "id": lease_area.id,
            "type": lease_area.type.value,
            "identifier": lease_area.identifier,
            "area": lease_area.area,
            "section_area": lease_area.section_area,
            "location": lease_area.location.value,
            "addresses": [
                {
                    "address": "Katu 1",
                    "postal_code": "00190",
                    "city": "Helsinki"
                },
                {
                    "address": "Katu 2",
                    "postal_code": "00190",
                    "city": "Helsinki"
                }
            ],
        }],
    }

    url = reverse('lease-detail', kwargs={'pk': lease.id})
    response = admin_client.patch(url, data=json.dumps(data, cls=DjangoJSONEncoder), content_type='application/json')

    assert response.status_code == 200, '%s %s' % (response.status_code, response.data)

    lease = Lease.objects.get(pk=response.data['id'])

    assert lease.lease_areas.count() == 1
    assert lease.lease_areas.first().addresses.count() == 2

    data = {
        "lease_areas": [{
            "id": lease_area.id,
            "type": lease_area.type.value,
            "identifier": lease_area.identifier,
            "area": lease_area.area,
            "section_area": lease_area.section_area,
            "location": lease_area.location.value,
            "addresses": None,
        }],
    }

    response = admin_client.patch(url, data=json.dumps(data, cls=DjangoJSONEncoder), content_type='application/json')

    assert response.status_code == 200, '%s %s' % (response.status_code, response.data)

    lease = Lease.objects.get(pk=response.data['id'])

    assert lease.lease_areas.count() == 1
    assert lease.lease_areas.first().addresses.count() == 0


@pytest.mark.django_db
def test_lease_area_plot_addresses(django_db_setup, admin_client, lease_test_data, assert_count_equal):
    lease = lease_test_data['lease']
    lease_area = lease.lease_areas.first()

    data = {
        "lease_areas": [{
            "id": lease_area.id,
            "type": lease_area.type.value,
            "identifier": lease_area.identifier,
            "area": lease_area.area,
            "section_area": lease_area.section_area,
            "location": lease_area.location.value,
            "plots": [{
                "identifier": "test",
                "type": "real_property",
                "area": 1234,
                "section_area": 500,
                "addresses": [
                    {
                        "address": "Katu 3",
                        "postal_code": "00120",
                        "city": "Helsinki"
                    },
                    {
                        "address": "Katu 4",
                        "postal_code": "00130",
                        "city": "Helsinki"
                    }
                ],
            }],
        }],
    }

    url = reverse('lease-detail', kwargs={'pk': lease.id})
    response = admin_client.patch(url, data=json.dumps(data, cls=DjangoJSONEncoder), content_type='application/json')

    assert response.status_code == 200, '%s %s' % (response.status_code, response.data)

    lease = Lease.objects.get(pk=response.data['id'])

    assert lease.lease_areas.first().plots.count() == 1
    assert lease.lease_areas.first().plots.first().addresses.count() == 2

    data = {
        "lease_areas": [{
            "id": lease_area.id,
            "type": lease_area.type.value,
            "identifier": lease_area.identifier,
            "area": lease_area.area,
            "section_area": lease_area.section_area,
            "location": lease_area.location.value,
            "plots": [{
                "identifier": "test",
                "type": "real_property",
                "area": 1234,
                "section_area": 500,
                "addresses": [],
            }],
        }],
    }

    url = reverse('lease-detail', kwargs={'pk': lease.id})
    response = admin_client.patch(url, data=json.dumps(data, cls=DjangoJSONEncoder), content_type='application/json')

    assert response.status_code == 200, '%s %s' % (response.status_code, response.data)

    lease = Lease.objects.get(pk=response.data['id'])

    assert lease.lease_areas.first().plots.count() == 1
    assert lease.lease_areas.first().plots.first().addresses.count() == 0
