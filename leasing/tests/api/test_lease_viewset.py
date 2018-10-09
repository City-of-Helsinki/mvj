import json

import pytest
from django.core.serializers.json import DjangoJSONEncoder
from django.urls import reverse

from leasing.models import Lease


@pytest.mark.django_db
@pytest.mark.parametrize("value, expected_value, expected_code", [
    ('', False, 500),
    (None, False, 500),
    (-1, False, 500),
    (0, False, 500),
    (1, False, 500),
    (5, False, 500),
    (True, True, 200),
    (False, False, 200),
])
def test_set_invoicing_state(django_db_setup, admin_client, lease_test_data, value, expected_value, expected_code):
    lease = lease_test_data['lease']

    assert lease.is_invoicing_enabled is False

    data = {
        "invoicing_enabled": value,
    }

    url = reverse('lease-set-invoicing-state', kwargs={
        'pk': lease.id
    })
    response = admin_client.post(url, data=json.dumps(data, cls=DjangoJSONEncoder), content_type='application/json')

    assert response.status_code == expected_code, '%s %s' % (response.status_code, response.data)

    lease = Lease.objects.get(pk=lease.id)

    assert lease.is_invoicing_enabled is expected_value


@pytest.mark.django_db
@pytest.mark.parametrize("value, expected_value, expected_code", [
    ('', False, 500),
    (None, False, 500),
    (-1, False, 500),
    (0, False, 500),
    (1, False, 500),
    (5, False, 500),
    (True, True, 200),
    (False, False, 200),
])
def test_set_rent_info_completion_state(django_db_setup, admin_client, lease_test_data, value, expected_value,
                                        expected_code):
    lease = lease_test_data['lease']

    assert lease.is_rent_info_complete is False

    data = {
        "rent_info_complete": value,
    }

    url = reverse('lease-set-rent-info-completion-state', kwargs={
        'pk': lease.id
    })
    response = admin_client.post(url, data=json.dumps(data, cls=DjangoJSONEncoder), content_type='application/json')

    assert response.status_code == expected_code, '%s %s' % (response.status_code, response.data)

    lease = Lease.objects.get(pk=lease.id)

    assert lease.is_rent_info_complete is expected_value
