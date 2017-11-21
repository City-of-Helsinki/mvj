import json

import pytest
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework.reverse import reverse
from rest_framework.test import APIClient, APITestCase


class LeaseTests(APITestCase):
    @pytest.mark.django_db(transaction=True)
    def get_client(self):

        user = get_user_model().objects.create(is_staff=True, is_superuser=True)
        user.save()

        token = Token()
        token.user = user
        token.save()

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        self.client = client
        return self.client

    def test_lease_dates(self):
        client = self.get_client()
        # set some invalid data where the end date is before the start date
        data = {
            'type': 'A1',
            'municipality': '1',
            'district': '01',
            'sequence': 1,
            'start_date': '2001-01-01',
            'end_date': '2000-01-01'
        }

        response = client.post(
            reverse('v1:lease-list'),
            json.dumps(data),
            content_type='application/json',
        )
        assert response.status_code == 400

        # fix the start date and try again
        data['start_date'] = '2000-01-01'
        response = client.post(
            reverse('v1:lease-list'),
            json.dumps(data),
            content_type='application/json',
        )
        assert response.status_code == 201
