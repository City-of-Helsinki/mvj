import pytest

from leasing.models import Lease


@pytest.mark.django_db
def test_lease_manager_get_by_identifier_invalid(django_db_setup, lease_test_data):
    with pytest.raises(RuntimeError) as e:
        Lease.objects.get_by_identifier('invalid')

    assert str(e.value) == 'identifier "invalid" doesn\'t match the identifier format'


@pytest.mark.django_db
def test_lease_manager_get_by_identifier_does_not_exist(django_db_setup, lease_test_data):
    with pytest.raises(Lease.DoesNotExist) as e:
        Lease.objects.get_by_identifier('A1111-1')

    assert str(e.value) == 'Lease matching query does not exist.'


@pytest.mark.django_db
def test_lease_manager_get_by_identifier_district_00(django_db_setup, lease_test_data):
    assert Lease.objects.get_by_identifier('A1100-1')


@pytest.mark.django_db
def test_lease_manager_get_by_identifier(django_db_setup, lease_factory):
    lease = lease_factory(
        type_id=1,
        municipality_id=1,
        district_id=5,
        notice_period_id=1,
    )

    assert Lease.objects.get_by_identifier('A1104-1') == lease


@pytest.mark.django_db
def test_lease_manager_get_by_identifier_zero_padded_sequence(django_db_setup, lease_factory):
    lease = lease_factory(
        type_id=1,
        municipality_id=1,
        district_id=5,
        notice_period_id=1,
    )

    assert Lease.objects.get_by_identifier('A1104-0001') == lease
