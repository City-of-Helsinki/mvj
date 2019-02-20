import json

import pytest
from django.contrib.auth.models import Permission
from django.core.serializers.json import DjangoJSONEncoder
from django.urls import reverse

from leasing.models import UiData


@pytest.mark.django_db
def test_create_own_uidata(django_db_setup, client, user_factory):
    user = user_factory(username='test_user', email="test_user@example.com")
    user.set_password('test_password')
    user.save()

    permission_names = [
        'add_uidata',
    ]

    for permission_name in permission_names:
        user.user_permissions.add(Permission.objects.get(codename=permission_name))

    client.login(username='test_user', password='test_password')
    url = reverse('ui_data-list')

    data = {
        "key": "testkey",
        "value": "testvalue",
    }

    response = client.post(url, data=json.dumps(data, cls=DjangoJSONEncoder), content_type='application/json')

    assert response.status_code == 201, '%s %s' % (response.status_code, response.data)

    uidata = UiData.objects.get(user=user)
    assert uidata.key == "testkey"


@pytest.mark.django_db
def test_cant_create_others_uidata(django_db_setup, client, user_factory):
    user = user_factory(username='test_user', email="test_user@example.com")
    user.set_password('test_password')
    user.save()

    permission_names = [
        'add_uidata',
    ]

    for permission_name in permission_names:
        user.user_permissions.add(Permission.objects.get(codename=permission_name))

    client.login(username='test_user', password='test_password')
    url = reverse('ui_data-list')

    user2 = user_factory(username='test_user2', email="test_user2@example.com")

    data = {
        "user": user2.id,
        "key": "testkey",
        "value": "testvalue",
    }

    response = client.post(url, data=json.dumps(data, cls=DjangoJSONEncoder), content_type='application/json')

    assert response.status_code == 403, '%s %s' % (response.status_code, response.data)


@pytest.mark.django_db
def test_can_create_global_uidata(django_db_setup, client, user_factory):
    user = user_factory(username='test_user', email="test_user@example.com")
    user.set_password('test_password')
    user.save()

    permission_names = [
        'add_uidata',
        'edit_global_ui_data',
    ]

    for permission_name in permission_names:
        user.user_permissions.add(Permission.objects.get(codename=permission_name))

    client.login(username='test_user', password='test_password')
    url = reverse('ui_data-list')

    data = {
        "user": None,
        "key": "testkey",
        "value": "testvalue",
    }

    response = client.post(url, data=json.dumps(data, cls=DjangoJSONEncoder), content_type='application/json')

    assert response.status_code == 201, '%s %s' % (response.status_code, response.data)

    uidata = UiData.objects.get(user=None)
    assert uidata.key == "testkey"


@pytest.mark.django_db
def test_cant_create_global_uidata(django_db_setup, client, user_factory):
    user = user_factory(username='test_user', email="test_user@example.com")
    user.set_password('test_password')
    user.save()

    permission_names = [
        'add_uidata',
    ]

    for permission_name in permission_names:
        user.user_permissions.add(Permission.objects.get(codename=permission_name))

    client.login(username='test_user', password='test_password')
    url = reverse('ui_data-list')

    data = {
        "user": None,
        "key": "testkey",
        "value": "testvalue",
    }

    response = client.post(url, data=json.dumps(data, cls=DjangoJSONEncoder), content_type='application/json')

    assert response.status_code == 403, '%s %s' % (response.status_code, response.data)
    assert UiData.objects.count() == 0


@pytest.mark.django_db
def test_can_edit_own_uidata(django_db_setup, client, user_factory, ui_data_factory):
    user = user_factory(username='test_user', email="test_user@example.com")
    user.set_password('test_password')
    user.save()

    permission_names = [
        'change_uidata',
    ]

    for permission_name in permission_names:
        user.user_permissions.add(Permission.objects.get(codename=permission_name))

    ui_data = ui_data_factory(user=user, key="testkey", value="testvalue")

    client.login(username='test_user', password='test_password')
    url = reverse('ui_data-detail', kwargs={
        "pk": ui_data.id
    })

    data = {
        "key": "testkey2",
        "value": "testvalue2",
    }

    response = client.patch(url, data=json.dumps(data, cls=DjangoJSONEncoder), content_type='application/json')

    assert response.status_code == 200, '%s %s' % (response.status_code, response.data)

    uidata = UiData.objects.get(id=ui_data.id)
    assert uidata.key == "testkey2"


@pytest.mark.django_db
def test_cant_edit_others_uidata(django_db_setup, client, user_factory, ui_data_factory):
    user = user_factory(username='test_user', email="test_user@example.com")
    user.set_password('test_password')
    user.save()

    permission_names = [
        'change_uidata',
    ]

    for permission_name in permission_names:
        user.user_permissions.add(Permission.objects.get(codename=permission_name))

    user2 = user_factory(username='test_user2', email="test_user2@example.com")

    ui_data = ui_data_factory(user=user2, key="testkey", value="testvalue")

    client.login(username='test_user', password='test_password')
    url = reverse('ui_data-detail', kwargs={
        "pk": ui_data.id
    })

    data = {
        "key": "testkey2",
        "value": "testvalue2",
    }

    response = client.patch(url, data=json.dumps(data, cls=DjangoJSONEncoder), content_type='application/json')

    assert response.status_code == 404, '%s %s' % (response.status_code, response.data)


@pytest.mark.django_db
def test_can_edit_global_uidata(django_db_setup, client, user_factory, ui_data_factory):
    user = user_factory(username='test_user', email="test_user@example.com")
    user.set_password('test_password')
    user.save()

    permission_names = [
        'change_uidata',
        'edit_global_ui_data',
    ]

    for permission_name in permission_names:
        user.user_permissions.add(Permission.objects.get(codename=permission_name))

    ui_data = ui_data_factory(user=None, key="testkey", value="testvalue")

    client.login(username='test_user', password='test_password')
    url = reverse('ui_data-detail', kwargs={
        "pk": ui_data.id
    })

    data = {
        "key": "testkey2",
        "value": "testvalue2",
    }

    response = client.patch(url, data=json.dumps(data, cls=DjangoJSONEncoder), content_type='application/json')

    assert response.status_code == 200, '%s %s' % (response.status_code, response.data)

    uidata = UiData.objects.get(id=ui_data.id)
    assert uidata.key == "testkey2"


@pytest.mark.django_db
def test_cant_edit_global_uidata(django_db_setup, client, user_factory, ui_data_factory):
    user = user_factory(username='test_user', email="test_user@example.com")
    user.set_password('test_password')
    user.save()

    permission_names = [
        'change_uidata',
    ]

    for permission_name in permission_names:
        user.user_permissions.add(Permission.objects.get(codename=permission_name))

    ui_data = ui_data_factory(user=None, key="testkey", value="testvalue")

    client.login(username='test_user', password='test_password')
    url = reverse('ui_data-detail', kwargs={
        "pk": ui_data.id
    })

    data = {
        "key": "testkey2",
        "value": "testvalue2",
    }

    response = client.patch(url, data=json.dumps(data, cls=DjangoJSONEncoder), content_type='application/json')

    assert response.status_code == 403, '%s %s' % (response.status_code, response.data)


@pytest.mark.django_db
def test_delete_own_uidata(django_db_setup, client, user_factory, ui_data_factory):
    user = user_factory(username='test_user', email="test_user@example.com")
    user.set_password('test_password')
    user.save()

    permission_names = [
        'delete_uidata',
    ]

    for permission_name in permission_names:
        user.user_permissions.add(Permission.objects.get(codename=permission_name))

    ui_data = ui_data_factory(user=user, key="testkey", value="testvalue")

    client.login(username='test_user', password='test_password')
    url = reverse('ui_data-detail', kwargs={"pk": ui_data.id})
    response = client.delete(url)

    assert response.status_code == 204, '%s %s' % (response.status_code, response.data)
    assert UiData.objects.count() == 0


@pytest.mark.django_db
def test_cant_delete_others_uidata(django_db_setup, client, user_factory, ui_data_factory):
    user = user_factory(username='test_user', email="test_user@example.com")
    user.set_password('test_password')
    user.save()

    permission_names = [
        'delete_uidata',
    ]

    for permission_name in permission_names:
        user.user_permissions.add(Permission.objects.get(codename=permission_name))

    user2 = user_factory(username='test_user2', email="test_user2@example.com")

    ui_data = ui_data_factory(user=user2, key="testkey", value="testvalue")

    client.login(username='test_user', password='test_password')
    url = reverse('ui_data-detail', kwargs={"pk": ui_data.id})
    response = client.delete(url)

    assert response.status_code == 404, '%s %s' % (response.status_code, response.data)
    assert UiData.objects.count() == 1
