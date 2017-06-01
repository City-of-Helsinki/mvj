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


@pytest.mark.django_db
def test_update_lease_add_note(user_factory, lease_factory):
    user1 = user_factory(username='user1', password='user1', email='user1@example.com', is_superuser=True)
    user2 = user_factory(username='user2', password='user2', email='user2@example.com')
    lease = lease_factory(state=LeaseState.DRAFT)

    api_client = APIClient()
    api_client.credentials(HTTP_AUTHORIZATION='Token ' + user1.username)

    url = reverse('v1:lease-detail', kwargs={'pk': lease.id})

    data = {
        'notes': [
            {
                'title': 'Test note title',
                'text': 'Test note text',
                'author': user2.id,
            },
        ],
    }

    response = api_client.patch(url, data=json.dumps(data), content_type='application/json')

    assert response.status_code == 200, '%s %s' % (response.status_code, response.data)
    assert len(lease.notes.all()) == 1
    assert lease.notes.first().title == 'Test note title'


@pytest.mark.django_db
def test_update_lease_remove_note(user_factory, lease_factory, note_factory):
    user1 = user_factory(username='user1', password='user1', email='user1@example.com', is_superuser=True)
    lease = lease_factory(state=LeaseState.DRAFT)

    note1 = note_factory(title='Existing note 1 title', text='Existing note 1 text')
    note2 = note_factory(title='Existing note 2 title', text='Existing note 2 text')

    lease.notes.set([note1, note2])

    assert len(lease.notes.all()) == 2

    api_client = APIClient()
    api_client.credentials(HTTP_AUTHORIZATION='Token ' + user1.username)

    url = reverse('v1:lease-detail', kwargs={'pk': lease.id})

    data = {
        'notes': [
            {
                'id': note2.id,
            },
            {
                'title': 'New note title',
                'text': 'New note text',
            },
        ],
    }

    response = api_client.patch(url, data=json.dumps(data), content_type='application/json')

    assert response.status_code == 200, '%s %s' % (response.status_code, response.data)
    assert len(lease.notes.all()) == 2
    assert sorted([note.title for note in lease.notes.all()]) == ['Existing note 2 title', 'New note title']
