import pytest
from django.contrib.auth.models import Permission
from django.urls import reverse


@pytest.mark.django_db
def test_anonymous_user_cannot_view_lease(django_db_setup, client, lease_test_data):
    url = reverse('lease-detail', kwargs={'pk': lease_test_data['lease'].id})

    response = client.get(url)

    assert response.status_code == 401, '%s %s' % (response.status_code, response.data)
    assert response.data['detail'].code == 'not_authenticated'


@pytest.mark.django_db
def test_user_without_permission_cant_view_lease(django_db_setup, client, lease_test_data, user_factory):
    user = user_factory(username='test_user')
    user.set_password('test_password')
    user.save()

    client.login(username='test_user', password='test_password')

    url = reverse('lease-detail', kwargs={'pk': lease_test_data['lease'].id})

    response = client.get(url)

    assert response.status_code == 403, '%s %s' % (response.status_code, response.data)
    assert response.data['detail'].code == 'permission_denied'


@pytest.mark.django_db
def test_user_with_permission_can_view_lease(django_db_setup, client, lease_test_data, user_factory):
    user = user_factory(username='test_user')
    user.set_password('test_password')
    user.save()

    permission = Permission.objects.get(codename='view_lease')
    user.user_permissions.add(permission)

    client.login(username='test_user', password='test_password')

    url = reverse('lease-detail', kwargs={'pk': lease_test_data['lease'].id})

    response = client.get(url)

    assert response.status_code == 200, '%s %s' % (response.status_code, response.data)
