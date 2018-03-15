import json

import pytest
from django.core.serializers.json import DjangoJSONEncoder
from django.urls import reverse
from django.utils import timezone

from leasing.models import Lease


@pytest.mark.django_db
def test_create_lease(django_db_setup, admin_client, contact_factory):
    test_contacts = [contact_factory(first_name="First name", last_name="Last name", is_lessor=True)]
    for i in range(3):
        test_contacts.append(contact_factory(first_name="First name " + str(i), last_name="Last name " + str(i)))

    data = {
        "state": "lease",
        "classification": "public",
        "intended_use_note": "Intended use note...",
        "transferable": True,
        "regulated": False,
        "notice_note": "Notice note...",
        "type": "A1",
        "municipality": 1,
        "district": 31,
        "intended_use": 1,
        "supportive_housing": 5,
        "statistical_use": 1,
        "financing": "A",
        "management": "1",
        "regulation": 1,
        "hitas": "0",
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
