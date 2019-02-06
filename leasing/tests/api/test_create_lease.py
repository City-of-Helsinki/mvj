import json

import pytest
from django.contrib.auth.models import Permission
from django.core.serializers.json import DjangoJSONEncoder
from django.urls import reverse
from django.utils import timezone

from leasing.enums import ContactType
from leasing.models import Lease


@pytest.mark.django_db
def test_create_lease(django_db_setup, admin_client, contact_factory):
    test_contacts = [contact_factory(first_name="First name", last_name="Last name", is_lessor=True,
                                     type=ContactType.PERSON)]
    for i in range(3):
        test_contacts.append(contact_factory(first_name="First name " + str(i), last_name="Last name " + str(i),
                                             type=ContactType.PERSON))

    data = {
        "state": "lease",
        "classification": "public",
        "intended_use_note": "Intended use note...",
        "transferable": True,
        "regulated": False,
        "notice_note": "Notice note...",
        "type": 1,
        "municipality": 1,
        "district": 31,
        "intended_use": 1,
        "supportive_housing": 5,
        "statistical_use": 1,
        "financing": 1,
        "management": 1,
        "regulation": 1,
        "hitas": 1,
        "notice_period": 1,
        "lessor": test_contacts[0].id,
        "tenants": [
            {
                "share_numerator": 1,
                "share_denominator": 2,
                "reference": "123",
                "tenantcontact_set": [
                    {
                        "type": "tenant",
                        "contact": test_contacts[1].id,
                        "start_date": timezone.now().date()
                    },
                    {
                        "type": "billing",
                        "contact": test_contacts[3].id,
                        "start_date": timezone.now().date()
                    }
                ]
            },
            {
                "share_numerator": 1,
                "share_denominator": 2,
                "reference": "345",
                "tenantcontact_set": [
                    {
                        "type": "tenant",
                        "contact": test_contacts[2].id,
                        "start_date": timezone.now().date()
                    }
                ]
            }
        ],
        "lease_areas": [
            {
                "identifier": "12345",
                "area": 100,
                "section_area": 100,
                "address": "Testaddress 1",
                "postal_code": "00100",
                "city": "Helsinki",
                "type": "real_property",
                "location": "surface",
                "plots": [
                    {
                        "identifier": "plot-1",
                        "area": 100,
                        "section_area": 100,
                        "address": "Test plotaddress 1",
                        "postal_code": "00100",
                        "city": "Helsinki",
                        "type": "real_property",
                        "registration_date": None,
                        "in_contract": True
                    }
                ]
            }
        ]
    }

    url = reverse('lease-list')

    response = admin_client.post(url, data=json.dumps(data, cls=DjangoJSONEncoder), content_type='application/json')

    assert response.status_code == 201, '%s %s' % (response.status_code, response.data)

    lease = Lease.objects.get(pk=response.data['id'])

    assert lease.identifier is not None
    assert lease.identifier.type == lease.type
    assert lease.identifier.municipality == lease.municipality
    assert lease.identifier.district == lease.district
    assert lease.identifier.sequence == 1

    assert lease.tenants.count() == 2

    t1 = lease.tenants.filter(reference="123").first()
    t2 = lease.tenants.filter(reference="345").first()
    assert t1.tenantcontact_set.all().count() == 2
    assert t2.tenantcontact_set.all().count() == 1

    assert lease.lease_areas.count() == 1
    assert lease.lease_areas.first().plots.count() == 1


@pytest.mark.django_db
def test_create_lease_relate_to_with_permission(django_db_setup, client, lease_test_data, user_factory):
    user = user_factory(username='test_user')
    user.set_password('test_password')
    user.save()

    permission_names = [
        'add_lease',
        'view_lease_id',
        'change_lease_identifier',
        'change_lease_type',
        'change_lease_municipality',
        'change_lease_district',
        'change_lease_related_leases',
    ]

    for permission_name in permission_names:
        user.user_permissions.add(Permission.objects.get(codename=permission_name))

    client.login(username='test_user', password='test_password')

    data = {
        "type": 1,
        "municipality": 1,
        "district": 11,
        "relate_to": lease_test_data["lease"].id,
        "relation_type": "transfer",
    }

    url = reverse('lease-list')

    response = client.post(url, data=json.dumps(data, cls=DjangoJSONEncoder), content_type='application/json')

    assert response.status_code == 201, '%s %s' % (response.status_code, response.data)

    lease = Lease.objects.get(pk=response.data['id'])

    assert len(response.data["related_leases"]["related_from"]) == 1
    assert lease_test_data["lease"].related_leases.count() == 1
    assert lease_test_data["lease"].related_leases.first().id == lease.id


@pytest.mark.django_db
def test_create_lease_relate_to_without_permission(django_db_setup, client, lease_test_data, user_factory):
    user = user_factory(username='test_user')
    user.set_password('test_password')
    user.save()

    permission_names = [
        'add_lease',
        'view_lease_id',
        'change_lease_identifier',
        'change_lease_type',
        'change_lease_municipality',
        'change_lease_district',
    ]

    for permission_name in permission_names:
        user.user_permissions.add(Permission.objects.get(codename=permission_name))

    client.login(username='test_user', password='test_password')

    data = {
        "type": 1,
        "municipality": 1,
        "district": 11,
        "relate_to": lease_test_data["lease"].id,
        "relation_type": "transfer",
    }

    url = reverse('lease-list')

    response = client.post(url, data=json.dumps(data, cls=DjangoJSONEncoder), content_type='application/json')

    assert response.status_code == 201, '%s %s' % (response.status_code, response.data)

    assert "related_leases" not in response.data
    assert lease_test_data["lease"].related_leases.count() == 0
