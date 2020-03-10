import json

import pytest
from django.contrib.auth.models import Permission
from django.core.serializers.json import DjangoJSONEncoder
from django.urls import reverse

from leasing.models import Lease


@pytest.mark.django_db
def test_create_lease(django_db_setup, admin_client, contact_factory, lease_data_dict_with_contacts):
    url = reverse('lease-list')

    response = admin_client.post(
        url, data=json.dumps(lease_data_dict_with_contacts, cls=DjangoJSONEncoder), content_type='application/json')

    assert response.status_code == 201, '%s %s' % (response.status_code, response.data)

    lease = Lease.objects.get(pk=response.data['id'])

    assert lease.identifier is not None
    assert lease.identifier.type == lease.type
    assert lease.identifier.municipality == lease.municipality
    assert lease.identifier.district == lease.district
    assert lease.identifier.sequence == 1

    assert lease.tenants.count() == 2

    t1 = lease.tenants.filter(reference="123").first()
    t2 = lease.tenants.filter(reference="345").first()
    assert t1.tenantcontact_set.all().count() == 2
    assert t2.tenantcontact_set.all().count() == 1

    assert lease.lease_areas.count() == 1
    assert lease.lease_areas.first().plots.count() == 1


@pytest.mark.django_db
def test_create_lease_relate_to_with_permission(django_db_setup, client, lease_test_data, user_factory):
    user = user_factory(username='test_user')
    user.set_password('test_password')
    user.save()

    permission_names = [
        'add_lease',
        'view_lease_id',
        'change_lease_identifier',
        'change_lease_type',
        'change_lease_municipality',
        'change_lease_district',
        'change_lease_related_leases',
    ]

    for permission_name in permission_names:
        user.user_permissions.add(Permission.objects.get(codename=permission_name))

    client.login(username='test_user', password='test_password')

    data = {
        "type": 1,
        "municipality": 1,
        "district": 11,
        "relate_to": lease_test_data["lease"].id,
        "relation_type": "transfer",
    }

    url = reverse('lease-list')

    response = client.post(url, data=json.dumps(data, cls=DjangoJSONEncoder), content_type='application/json')

    assert response.status_code == 201, '%s %s' % (response.status_code, response.data)

    lease = Lease.objects.get(pk=response.data['id'])

    assert len(response.data["related_leases"]["related_from"]) == 1
    assert lease_test_data["lease"].related_leases.count() == 1
    assert lease_test_data["lease"].related_leases.first().id == lease.id


@pytest.mark.django_db
def test_create_lease_relate_to_without_permission(django_db_setup, client, lease_test_data, user_factory):
    user = user_factory(username='test_user')
    user.set_password('test_password')
    user.save()

    permission_names = [
        'add_lease',
        'view_lease_id',
        'change_lease_identifier',
        'change_lease_type',
        'change_lease_municipality',
        'change_lease_district',
    ]

    for permission_name in permission_names:
        user.user_permissions.add(Permission.objects.get(codename=permission_name))

    client.login(username='test_user', password='test_password')

    data = {
        "type": 1,
        "municipality": 1,
        "district": 11,
        "relate_to": lease_test_data["lease"].id,
        "relation_type": "transfer",
    }

    url = reverse('lease-list')

    response = client.post(url, data=json.dumps(data, cls=DjangoJSONEncoder), content_type='application/json')

    assert response.status_code == 201, '%s %s' % (response.status_code, response.data)

    assert "related_leases" not in response.data
    assert lease_test_data["lease"].related_leases.count() == 0


@pytest.mark.django_db
def test_create_lease_with_basis_of_rents(
    django_db_setup, admin_client, contact_factory, lease_data_dict_with_contacts
):
    url = reverse("lease-list")
    lease_data_dict_with_contacts["basis_of_rents"] = [
        {"intended_use": 1, "area": "101.00", "area_unit": "m2"}
    ]
    response = admin_client.post(
        url,
        data=json.dumps(lease_data_dict_with_contacts, cls=DjangoJSONEncoder),
        content_type="application/json",
    )

    assert response.status_code == 201, "%s %s" % (response.status_code, response.data)


def test_create_lease_with_basis_of_rents_fail_without_intended_use(
    django_db_setup, admin_client, contact_factory, lease_data_dict_with_contacts
):
    url = reverse("lease-list")
    lease_data_dict_with_contacts["basis_of_rents"] = [
        {"area": "101.00", "area_unit": "m2"}
    ]
    response = admin_client.post(
        url,
        data=json.dumps(lease_data_dict_with_contacts, cls=DjangoJSONEncoder),
        content_type="application/json",
    )

    assert response.status_code == 400, "%s %s" % (response.status_code, response.data)


def test_create_lease_with_basis_of_rents_fail_without_area(
    django_db_setup, admin_client, contact_factory, lease_data_dict_with_contacts
):
    url = reverse("lease-list")
    lease_data_dict_with_contacts["basis_of_rents"] = [
        {"intended_use": 1, "area_unit": "m2"}
    ]
    response = admin_client.post(
        url,
        data=json.dumps(lease_data_dict_with_contacts, cls=DjangoJSONEncoder),
        content_type="application/json",
    )

    assert response.status_code == 400, "%s %s" % (response.status_code, response.data)


def test_create_lease_with_basis_of_rents_fail_without_area_unit(
    django_db_setup, admin_client, contact_factory, lease_data_dict_with_contacts
):
    url = reverse("lease-list")
    lease_data_dict_with_contacts["basis_of_rents"] = [
        {"intended_use": 1, "area": "101.00"}
    ]
    response = admin_client.post(
        url,
        data=json.dumps(lease_data_dict_with_contacts, cls=DjangoJSONEncoder),
        content_type="application/json",
    )

    assert response.status_code == 400, "%s %s" % (response.status_code, response.data)
