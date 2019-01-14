import pytest
from django.contrib.auth.models import Permission
from django.urls import reverse

from leasing.models import Lease
from leasing.serializers.lease import LeaseRetrieveSerializer


@pytest.mark.django_db
def test_user_cant_view_any_fields(django_db_setup, client, lease_test_data, user_factory):
    user = user_factory(username='test_user')
    user.set_password('test_password')
    user.save()

    permission = Permission.objects.get(codename='view_lease')
    user.user_permissions.add(permission)

    client.login(username='test_user', password='test_password')

    url = reverse('lease-detail', kwargs={'pk': lease_test_data['lease'].id})

    response = client.get(url)

    assert response.status_code == 200, '{} {}'.format(response.status_code, response.data)
    assert response.data == {}


@pytest.mark.django_db
def test_superuser_can_view_all_fields(django_db_setup, client, lease_test_data, user_factory):
    user = user_factory(username='test_user')
    user.set_password('test_password')
    user.is_superuser = True
    user.save()

    client.login(username='test_user', password='test_password')

    url = reverse('lease-detail', kwargs={'pk': lease_test_data['lease'].id})

    response = client.get(url)

    assert response.status_code == 200, '{} {}'.format(response.status_code, response.data)
    assert sorted(response.data.keys()) == sorted(LeaseRetrieveSerializer().get_fields().keys())


@pytest.mark.django_db
def test_user_can_view_some_fields(django_db_setup, client, lease_test_data, user_factory):
    user = user_factory(username='test_user')
    user.set_password('test_password')
    user.save()

    user.user_permissions.add(Permission.objects.get(codename='view_lease'))

    field_names = ['id', 'start_date', 'end_date', 'state']
    for field_name in field_names:
        codename = 'view_lease_{}'.format(field_name)
        user.user_permissions.add(Permission.objects.get(codename=codename))

    client.login(username='test_user', password='test_password')

    url = reverse('lease-detail', kwargs={'pk': lease_test_data['lease'].id})

    response = client.get(url)

    assert response.status_code == 200, '{} {}'.format(response.status_code, response.data)
    assert sorted(response.data.keys()) == ['end_date', 'id', 'start_date', 'state']


@pytest.mark.django_db
def test_user_cannot_modify_field(django_db_setup, client, lease_test_data, user_factory):
    user = user_factory(username='test_user')
    user.set_password('test_password')
    user.save()

    user.user_permissions.add(Permission.objects.get(codename='change_lease'))
    user.user_permissions.add(Permission.objects.get(codename='view_lease_type'))

    client.login(username='test_user', password='test_password')

    url = reverse('lease-detail', kwargs={
        'pk': lease_test_data['lease'].id
    })

    assert lease_test_data['lease'].type.id != 2

    data = {
        'type': 2,
    }

    response = client.patch(url, data=data, content_type='application/json')

    lease = Lease.objects.get(pk=lease_test_data['lease'].id)

    assert response.status_code == 200, '{} {}'.format(response.status_code, response.data)
    assert lease.type_id == 1


@pytest.mark.django_db
def test_user_can_modify_field(django_db_setup, client, lease_test_data, user_factory):
    user = user_factory(username='test_user')
    user.set_password('test_password')
    user.save()

    user.user_permissions.add(Permission.objects.get(codename='change_lease'))
    user.user_permissions.add(Permission.objects.get(codename='change_lease_type'))

    client.login(username='test_user', password='test_password')

    url = reverse('lease-detail', kwargs={'pk': lease_test_data['lease'].id})

    assert lease_test_data['lease'].type.id != 2

    data = {
        'type': 2,
    }

    response = client.patch(url, data=data, content_type='application/json')

    lease = Lease.objects.get(pk=lease_test_data['lease'].id)

    assert response.status_code == 200, '{} {}'.format(response.status_code, response.data)
    assert lease.type_id == 2
