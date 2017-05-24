import json

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from leasing.enums import LeaseState


@pytest.mark.django_db
def test_update_lease(user_factory, lease_factory):
    user1 = user_factory(username='user1', password='user1', email='user1@example.com', is_superuser=True)
    lease = lease_factory(state=LeaseState.DRAFT)

    api_client = APIClient()
    api_client.credentials(HTTP_AUTHORIZATION='Token ' + user1.username)

    url = reverse('v1:lease-detail', kwargs={'pk': lease.id})

    data = {
        'rents': [
            {
                'amount': '1000.00',
                'end_date': None,
                'lease': 1,
                'start_date': None,
                'type': 'free',
                'use': 'Test use',
            },
        ],
        'conditions': [
            {
                'lease': lease.id,
                'type': 'other',
                'description': 'Test condition',
            }
        ],
    }

    response = api_client.patch(url, data=json.dumps(data), content_type='application/json')

    assert response.status_code == 200, '%s %s' % (response.status_code, response.data)
    assert len(lease.rents.all()) == 1
    assert lease.rents.first().use == 'Test use'

    assert len(lease.conditions.all()) == 1
    assert lease.conditions.first().description == 'Test condition'
