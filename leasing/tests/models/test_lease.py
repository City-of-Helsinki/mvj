import datetime

import pytest

from leasing.enums import ContactType, TenantContactType
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


@pytest.mark.django_db
def test_get_tenant_shares_for_period(django_db_setup, lease_factory, contact_factory, tenant_factory,
                                      tenant_contact_factory, assert_count_equal):
    """Lease with two tenants without billing contacts"""
    lease = lease_factory(type_id=1, municipality_id=1, district_id=1, notice_period_id=1)

    tenant1 = tenant_factory(lease=lease, share_numerator=1, share_denominator=2)
    tenant2 = tenant_factory(lease=lease, share_numerator=1, share_denominator=2)

    contact1 = contact_factory(first_name="First name 1", last_name="Last name 1", type=ContactType.PERSON)
    contact2 = contact_factory(first_name="First name 2", last_name="Last name 2", type=ContactType.PERSON)

    tenant_contact_factory(type=TenantContactType.TENANT, tenant=tenant1, contact=contact1,
                           start_date=datetime.date(year=2017, month=1, day=1)),
    tenant_contact_factory(type=TenantContactType.TENANT, tenant=tenant2, contact=contact2,
                           start_date=datetime.date(year=2017, month=1, day=1)),

    start_date = datetime.date(year=2017, month=1, day=1)
    end_date = datetime.date(year=2017, month=12, day=31)

    shares = lease.get_tenant_shares_for_period(start_date, end_date)

    assert len(shares) == 2
    assert_count_equal(shares.keys(), [contact1, contact2])
    assert shares[contact1] == {
        tenant1: [(start_date, end_date)]
    }
    assert shares[contact2] == {
        tenant2: [(start_date, end_date)]
    }


@pytest.mark.django_db
def test_get_tenant_shares_for_period_one_billing(django_db_setup, lease_factory, contact_factory, tenant_factory,
                                                  tenant_contact_factory, assert_count_equal):
    """Lease with two tenants. Tenant2's billing contact is contact1"""
    lease = lease_factory(type_id=1, municipality_id=1, district_id=1, notice_period_id=1)

    tenant1 = tenant_factory(lease=lease, share_numerator=1, share_denominator=2)
    tenant2 = tenant_factory(lease=lease, share_numerator=1, share_denominator=2)

    contact1 = contact_factory(first_name="First name 1", last_name="Last name 1", type=ContactType.PERSON)
    contact2 = contact_factory(first_name="First name 2", last_name="Last name 2", type=ContactType.PERSON)

    tenant_contact_factory(type=TenantContactType.TENANT, tenant=tenant1, contact=contact1,
                           start_date=datetime.date(year=2017, month=1, day=1)),
    tenant_contact_factory(type=TenantContactType.TENANT, tenant=tenant2, contact=contact2,
                           start_date=datetime.date(year=2017, month=1, day=1)),
    tenant_contact_factory(type=TenantContactType.BILLING, tenant=tenant2, contact=contact1,
                           start_date=datetime.date(year=2017, month=1, day=1)),

    start_date = datetime.date(year=2017, month=1, day=1)
    end_date = datetime.date(year=2017, month=12, day=31)

    shares = lease.get_tenant_shares_for_period(start_date, end_date)

    assert len(shares) == 1
    assert_count_equal(shares.keys(), [contact1])
    assert shares[contact1] == {
        tenant1: [(start_date, end_date)],
        tenant2: [(start_date, end_date)]
    }


@pytest.mark.django_db
def test_get_tenant_shares_for_period_change_tenant(django_db_setup, lease_factory, contact_factory, tenant_factory,
                                                    tenant_contact_factory, assert_count_equal):
    """Lease with two tenants. Tenant2 changes to tenant3 mid-year"""
    lease = lease_factory(type_id=1, municipality_id=1, district_id=1, notice_period_id=1)

    tenant1 = tenant_factory(lease=lease, share_numerator=1, share_denominator=2)
    tenant2 = tenant_factory(lease=lease, share_numerator=1, share_denominator=2)
    tenant3 = tenant_factory(lease=lease, share_numerator=1, share_denominator=2)

    contact1 = contact_factory(first_name="First name 1", last_name="Last name 1", type=ContactType.PERSON)
    contact2 = contact_factory(first_name="First name 2", last_name="Last name 2", type=ContactType.PERSON)
    contact3 = contact_factory(first_name="First name 3", last_name="Last name 3", type=ContactType.PERSON)

    tenant_contact_factory(type=TenantContactType.TENANT, tenant=tenant1, contact=contact1,
                           start_date=datetime.date(year=2017, month=1, day=1)),
    tenant_contact_factory(type=TenantContactType.TENANT, tenant=tenant2, contact=contact2,
                           start_date=datetime.date(year=2017, month=1, day=1),
                           end_date=datetime.date(year=2017, month=6, day=30)),
    tenant_contact_factory(type=TenantContactType.TENANT, tenant=tenant3, contact=contact3,
                           start_date=datetime.date(year=2017, month=7, day=1)),

    start_date = datetime.date(year=2017, month=1, day=1)
    end_date = datetime.date(year=2017, month=12, day=31)

    shares = lease.get_tenant_shares_for_period(start_date, end_date)

    assert len(shares) == 3
    assert_count_equal(shares.keys(), [contact1, contact2, contact3])
    assert shares[contact1] == {
        tenant1: [(start_date, end_date)]
    }
    assert shares[contact2] == {
        tenant2: [(start_date, datetime.date(year=2017, month=6, day=30))]
    }
    assert shares[contact3] == {
        tenant3: [(datetime.date(year=2017, month=7, day=1), end_date)]
    }
