import pytest
from django.urls import reverse
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_regular_user_should_not_be_allowed_to_delete_an_application(user_factory, application_factory):
    user1 = user_factory(username='user1', password='user1', email='user1@example.com')

    application1 = application_factory(type="other")

    api_client = APIClient()
    api_client.credentials(HTTP_AUTHORIZATION='Token ' + user1.username)

    url = reverse('v1:application-detail', kwargs={'pk': application1.pk})

    response = api_client.delete(url)

    assert response.status_code == 403, '%s %s' % (response.status_code, response.data)


@pytest.mark.django_db
def test_superuser_should_be_allowed_to_delete_an_application(user_factory, application_factory):
    user1 = user_factory(username='user1', password='user1', email='user1@example.com', is_superuser=True)

    application1 = application_factory(type="other")

    api_client = APIClient()
    api_client.credentials(HTTP_AUTHORIZATION='Token ' + user1.username)

    url = reverse('v1:application-detail', kwargs={'pk': application1.pk})

    response = api_client.delete(url)

    assert response.status_code == 204, '%s %s' % (response.status_code, response.data)
