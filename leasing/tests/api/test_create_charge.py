import datetime
from decimal import Decimal

import pytest

from leasing.enums import ContactType, TenantContactType
from leasing.serializers.invoice import CreateChargeSerializer


@pytest.mark.django_db
def test_create_charge_one_tenant_one_row(django_db_setup, lease_factory, tenant_factory, tenant_rent_share_factory,
                                          contact_factory, tenant_contact_factory):
    lease = lease_factory(type_id=1, municipality_id=1, district_id=1, notice_period_id=1,
                          start_date=datetime.date(year=2000, month=1, day=1))

    tenant1 = tenant_factory(lease=lease, share_numerator=1, share_denominator=1)
    tenant_rent_share_factory(tenant=tenant1, intended_use_id=1, share_numerator=1, share_denominator=1)
    contact1 = contact_factory(first_name="First name 1", last_name="Last name 1", type=ContactType.PERSON)
    tenant_contact_factory(type=TenantContactType.TENANT, tenant=tenant1, contact=contact1,
                           start_date=datetime.date(year=2000, month=1, day=1))

    data = {
        'lease': lease.id,
        'due_date': '2019-01-01',
        'rows': [
            {
                'amount': Decimal(10),
                'receivable_type': 1,
            }
        ],
    }

    serializer = CreateChargeSerializer(data=data)
    serializer.is_valid(raise_exception=True)
    serializer.save()

    assert lease.invoices.count() == 1

    invoice = lease.invoices.first()

    assert invoice.recipient == contact1
    assert invoice.total_amount == Decimal(10)
    assert invoice.rows.count() == 1

    row = invoice.rows.first()

    assert row.tenant == tenant1
    assert row.amount == Decimal(10)


@pytest.mark.django_db
def test_create_charge_one_tenant_two_rows(django_db_setup, assert_count_equal, lease_factory, tenant_factory,
                                           tenant_rent_share_factory, contact_factory, tenant_contact_factory):
    lease = lease_factory(type_id=1, municipality_id=1, district_id=1, notice_period_id=1,
                          start_date=datetime.date(year=2000, month=1, day=1))

    tenant1 = tenant_factory(lease=lease, share_numerator=1, share_denominator=1)
    tenant_rent_share_factory(tenant=tenant1, intended_use_id=1, share_numerator=1, share_denominator=1)
    contact1 = contact_factory(first_name="First name 1", last_name="Last name 1", type=ContactType.PERSON)
    tenant_contact_factory(type=TenantContactType.TENANT, tenant=tenant1, contact=contact1,
                           start_date=datetime.date(year=2000, month=1, day=1))

    data = {
        'lease': lease.id,
        'due_date': '2019-01-01',
        'rows': [
            {
                'amount': Decimal(10),
                'receivable_type': 1,
            },
            {
                'amount': Decimal(20),
                'receivable_type': 2,
            }
        ],
    }

    serializer = CreateChargeSerializer(data=data)
    serializer.is_valid(raise_exception=True)
    serializer.save()

    assert lease.invoices.count() == 1

    invoice = lease.invoices.first()

    assert invoice.recipient == contact1
    assert invoice.total_amount == Decimal(30)
    assert invoice.rows.count() == 2

    row_amounts = [r.amount for r in invoice.rows.all()]
    assert_count_equal(row_amounts, [Decimal(10), Decimal(20)])


@pytest.mark.django_db
def test_create_charge_three_tenants_one_row(django_db_setup, assert_count_equal, lease_factory, tenant_factory,
                                             tenant_rent_share_factory, contact_factory, tenant_contact_factory):
    lease = lease_factory(type_id=1, municipality_id=1, district_id=1, notice_period_id=1,
                          start_date=datetime.date(year=2000, month=1, day=1))

    tenant1 = tenant_factory(lease=lease, share_numerator=1, share_denominator=3)
    tenant_rent_share_factory(tenant=tenant1, intended_use_id=1, share_numerator=1, share_denominator=3)
    contact1 = contact_factory(first_name="First name 1", last_name="Last name 1", type=ContactType.PERSON)
    tenant_contact_factory(type=TenantContactType.TENANT, tenant=tenant1, contact=contact1,
                           start_date=datetime.date(year=2000, month=1, day=1))

    tenant2 = tenant_factory(lease=lease, share_numerator=1, share_denominator=3)
    tenant_rent_share_factory(tenant=tenant2, intended_use_id=1, share_numerator=1, share_denominator=3)
    contact2 = contact_factory(first_name="First name 2", last_name="Last name 2", type=ContactType.PERSON)
    tenant_contact_factory(type=TenantContactType.TENANT, tenant=tenant2, contact=contact2,
                           start_date=datetime.date(year=2000, month=1, day=1))

    tenant3 = tenant_factory(lease=lease, share_numerator=1, share_denominator=3)
    tenant_rent_share_factory(tenant=tenant3, intended_use_id=1, share_numerator=1, share_denominator=3)
    contact3 = contact_factory(first_name="First name 3", last_name="Last name 3", type=ContactType.PERSON)
    tenant_contact_factory(type=TenantContactType.TENANT, tenant=tenant3, contact=contact3,
                           start_date=datetime.date(year=2000, month=1, day=1))

    data = {
        'lease': lease.id,
        'due_date': '2019-01-01',
        'rows': [
            {
                'amount': Decimal(100),
                'receivable_type': 1,
            },
        ],
    }

    serializer = CreateChargeSerializer(data=data)
    serializer.is_valid(raise_exception=True)
    serializer.save()

    assert lease.invoices.count() == 3

    total_sum = sum([i.billed_amount for i in lease.invoices.all()])
    assert total_sum == Decimal(100)

    billed_amounts = [i.billed_amount for i in lease.invoices.all()]
    assert_count_equal(billed_amounts, [Decimal('33.33'), Decimal('33.33'), Decimal('33.34')])

    total_sums = [i.total_amount for i in lease.invoices.all()]
    assert_count_equal(total_sums, [Decimal(100), Decimal(100), Decimal(100)])


@pytest.mark.django_db
def test_create_charge_three_tenants_two_rows(django_db_setup, assert_count_equal, lease_factory, tenant_factory,
                                              tenant_rent_share_factory, contact_factory, tenant_contact_factory):
    lease = lease_factory(type_id=1, municipality_id=1, district_id=1, notice_period_id=1,
                          start_date=datetime.date(year=2000, month=1, day=1))

    tenant1 = tenant_factory(lease=lease, share_numerator=1, share_denominator=3)
    tenant_rent_share_factory(tenant=tenant1, intended_use_id=1, share_numerator=1, share_denominator=3)
    contact1 = contact_factory(first_name="First name 1", last_name="Last name 1", type=ContactType.PERSON)
    tenant_contact_factory(type=TenantContactType.TENANT, tenant=tenant1, contact=contact1,
                           start_date=datetime.date(year=2000, month=1, day=1))

    tenant2 = tenant_factory(lease=lease, share_numerator=1, share_denominator=3)
    tenant_rent_share_factory(tenant=tenant2, intended_use_id=1, share_numerator=1, share_denominator=3)
    contact2 = contact_factory(first_name="First name 2", last_name="Last name 2", type=ContactType.PERSON)
    tenant_contact_factory(type=TenantContactType.TENANT, tenant=tenant2, contact=contact2,
                           start_date=datetime.date(year=2000, month=1, day=1))

    tenant3 = tenant_factory(lease=lease, share_numerator=1, share_denominator=3)
    tenant_rent_share_factory(tenant=tenant3, intended_use_id=1, share_numerator=1, share_denominator=3)
    contact3 = contact_factory(first_name="First name 3", last_name="Last name 3", type=ContactType.PERSON)
    tenant_contact_factory(type=TenantContactType.TENANT, tenant=tenant3, contact=contact3,
                           start_date=datetime.date(year=2000, month=1, day=1))

    data = {
        'lease': lease.id,
        'due_date': '2019-01-01',
        'rows': [
            {
                'amount': Decimal(100),
                'receivable_type': 1,
            },
            {
                'amount': Decimal(10),
                'receivable_type': 2,
            }
        ],
    }

    serializer = CreateChargeSerializer(data=data)
    serializer.is_valid(raise_exception=True)
    serializer.save()

    assert lease.invoices.count() == 3

    total_sum = sum([i.billed_amount for i in lease.invoices.all()])
    assert total_sum == Decimal(110)

    total_sums = [i.total_amount for i in lease.invoices.all()]
    assert_count_equal(total_sums, [Decimal(110), Decimal(110), Decimal(110)])
