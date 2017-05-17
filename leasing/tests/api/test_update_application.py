import json

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from leasing.enums import ApplicationType


@pytest.mark.django_db
def test_update_application_add_note(user_factory, application_factory, note_factory):
    user1 = user_factory(username='user1', password='user1', email='user1@example.com', is_superuser=True)
    application = application_factory(type=ApplicationType.DETACHED_HOUSE)

    assert len(application.notes.all()) == 0

    api_client = APIClient()
    api_client.credentials(HTTP_AUTHORIZATION='Token ' + user1.username)

    url = reverse('v1:application-detail', kwargs={'pk': application.id})

    data = {
        'notes': [
            {
                'title': 'Application test note',
                'text': 'Application test note text',
            },
        ],
    }

    response = api_client.patch(url, data=json.dumps(data), content_type='application/json')

    assert response.status_code == 200, '%s %s' % (response.status_code, response.data)
    assert len(application.notes.all()) == 1
    assert application.notes.first().title == 'Application test note'


@pytest.mark.django_db
def test_update_application_update_note(user_factory, application_factory, note_factory):
    user1 = user_factory(username='user1', password='user1', email='user1@example.com', is_superuser=True)
    application = application_factory(type=ApplicationType.DETACHED_HOUSE)
    note = note_factory(title='Existing note title', text='Existing note text')

    application.notes.add(note)

    api_client = APIClient()
    api_client.credentials(HTTP_AUTHORIZATION='Token ' + user1.username)

    url = reverse('v1:application-detail', kwargs={'pk': application.id})

    data = {
        'notes': [
            {
                'id': note.id,
                'text': 'Edited text',
            },
        ],
    }

    response = api_client.patch(url, data=json.dumps(data), content_type='application/json')

    assert response.status_code == 200, '%s %s' % (response.status_code, response.data)
    assert len(application.notes.all()) == 1
    assert application.notes.first().id == note.id
    assert application.notes.first().title == 'Existing note title'
    assert application.notes.first().text == 'Edited text'
