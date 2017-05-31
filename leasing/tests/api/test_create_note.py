import json

import pytest
from django.urls import reverse
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_create_note_with_author_dict(user_factory, application_factory):
    user1 = user_factory(username='user1', password='user1', email='user1@example.com', is_superuser=True)

    data = {
        'title': 'Test note title',
        'text': 'Test note text',
        'author': {
            'id': user1.id,
        }
    }

    api_client = APIClient()
    api_client.credentials(HTTP_AUTHORIZATION='Token ' + user1.username)

    url = reverse('v1:note-list')

    response = api_client.post(url, data=json.dumps(data), content_type='application/json')

    assert response.status_code == 201, '%s %s' % (response.status_code, response.data)


@pytest.mark.django_db
def test_create_note_with_author_id(user_factory, application_factory):
    user1 = user_factory(username='user1', password='user1', email='user1@example.com', is_superuser=True)

    data = {
        'title': 'Test note title',
        'text': 'Test note text',
        'author': user1.id,
    }

    api_client = APIClient()
    api_client.credentials(HTTP_AUTHORIZATION='Token ' + user1.username)

    url = reverse('v1:note-list')

    response = api_client.post(url, data=json.dumps(data), content_type='application/json')

    assert response.status_code == 201, '%s %s' % (response.status_code, response.data)
