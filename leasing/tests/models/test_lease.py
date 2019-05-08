import datetime
from decimal import Decimal

import pytest

from leasing.enums import (
    ContactType, DueDatesType, InvoiceState, InvoiceType, PeriodType, RentCycle, RentType, TenantContactType)
from leasing.models import Invoice, Lease, ReceivableType


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
                           start_date=datetime.date(year=2017, month=1, day=1))
    tenant_contact_factory(type=TenantContactType.TENANT, tenant=tenant2, contact=contact2,
                           start_date=datetime.date(year=2017, month=1, day=1))

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
                           start_date=datetime.date(year=2017, month=1, day=1))
    tenant_contact_factory(type=TenantContactType.TENANT, tenant=tenant2, contact=contact2,
                           start_date=datetime.date(year=2017, month=1, day=1))
    tenant_contact_factory(type=TenantContactType.BILLING, tenant=tenant2, contact=contact1,
                           start_date=datetime.date(year=2017, month=1, day=1))

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
                           start_date=datetime.date(year=2017, month=1, day=1))
    tenant_contact_factory(type=TenantContactType.TENANT, tenant=tenant2, contact=contact2,
                           start_date=datetime.date(year=2017, month=1, day=1),
                           end_date=datetime.date(year=2017, month=6, day=30))
    tenant_contact_factory(type=TenantContactType.TENANT, tenant=tenant3, contact=contact3,
                           start_date=datetime.date(year=2017, month=7, day=1))

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


@pytest.mark.django_db
def test_credit_rent_after_end(django_db_setup, lease_factory, contact_factory, tenant_factory,
                               tenant_contact_factory, invoice_factory, invoice_row_factory, rent_factory,
                               contract_rent_factory):
    lease = lease_factory(type_id=1, municipality_id=1, district_id=1, notice_period_id=1,
                          start_date=datetime.date(year=2000, month=1, day=1))

    tenant1 = tenant_factory(lease=lease, share_numerator=1, share_denominator=1)

    contact1 = contact_factory(first_name="First name 1", last_name="Last name 1", type=ContactType.PERSON)

    tenant_contact_factory(type=TenantContactType.TENANT, tenant=tenant1, contact=contact1,
                           start_date=datetime.date(year=2000, month=1, day=1))

    rent = rent_factory(
        lease=lease,
        type=RentType.FIXED,
        cycle=RentCycle.JANUARY_TO_DECEMBER,
        due_dates_type=DueDatesType.FIXED,
        due_dates_per_year=1,
    )

    contract_rent_factory(
        rent=rent,
        intended_use_id=1,
        amount=1000,
        period=PeriodType.PER_MONTH,
        base_amount=1000,
        base_amount_period=PeriodType.PER_MONTH,
    )

    billing_period_start_date = datetime.date(year=2017, month=1, day=1)
    billing_period_end_date = datetime.date(year=2017, month=12, day=31)

    invoice = invoice_factory(
        lease=lease,
        type=InvoiceType.CHARGE,
        total_amount=Decimal('12000'),
        billed_amount=Decimal('12000'),
        outstanding_amount=Decimal('0'),
        recipient=contact1,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
        state=InvoiceState.PAID,
        generated=True,
    )

    receivable_type = ReceivableType.objects.get(pk=1)

    invoice_row_factory(
        invoice=invoice,
        receivable_type=receivable_type,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
        tenant=tenant1,
        amount=Decimal('200'),
    )

    lease.end_date = datetime.date(year=2017, month=6, day=30)
    lease.save()

    lease.credit_rent_after_end()

    credit_note = Invoice.objects.get(lease=lease, type=InvoiceType.CREDIT_NOTE)

    assert credit_note.total_amount == Decimal(6000)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "notes, expected",
    [
        (
            [],
            '',
        ),
        # Non-matching notes
        (
            [
                {
                    'start': '20180101',
                    'end': '20181231',
                    'notes': 'Test note',
                },
            ],
            '',
        ),
        (
            [
                {
                    'start': '20160101',
                    'end': '20161231',
                    'notes': 'Test note',
                },
            ],
            '',
        ),
        (
            [
                {
                    'start': '20180101',
                    'end': '20181231',
                    'notes': 'Test note',
                },
                {
                    'start': '20160101',
                    'end': '20161231',
                    'notes': 'Test note',
                },
            ],
            '',
        ),
        # Matching notes
        (
            [
                {
                    'start': '20170101',
                    'end': '20171231',
                    'notes': 'Test note',
                },
            ],
            'Test note',
        ),
        (
            [
                {
                    'start': '20170101',
                    'end': '20171231',
                    'notes': 'Test note',
                },
                {
                    'start': '20170101',
                    'end': '20171231',
                    'notes': 'Test note2',
                },
            ],
            'Test note Test note2',
        ),
        # Matching and non-matching
        (
            [
                {
                    'start': '20170101',
                    'end': '20171231',
                    'notes': 'Test note',
                },
                {
                    'start': '20180101',
                    'end': '20181231',
                    'notes': 'Test note2',
                },
            ],
            'Test note',
        ),
        (
            [
                {
                    'start': '20160101',
                    'end': '20161231',
                    'notes': 'Test note',
                },
                {
                    'start': '20170101',
                    'end': '20171231',
                    'notes': 'Test note2',
                },
                {
                    'start': '20170101',
                    'end': '20171231',
                    'notes': 'Test note3',
                },
                {
                    'start': '20180101',
                    'end': '20181231',
                    'notes': 'Test note4',
                },
            ],
            'Test note2 Test note3',
        ),
    ]
)
def test_calculate_invoices_invoice_note(django_db_setup, lease_factory, contact_factory, tenant_factory,
                                         tenant_contact_factory, rent_factory, contract_rent_factory,
                                         invoice_note_factory, notes, expected):
    lease = lease_factory(type_id=1, municipality_id=1, district_id=1, notice_period_id=1,
                          start_date=datetime.date(year=2000, month=1, day=1))

    tenant1 = tenant_factory(lease=lease, share_numerator=1, share_denominator=1)

    contact1 = contact_factory(first_name="First name 1", last_name="Last name 1", type=ContactType.PERSON)

    tenant_contact_factory(type=TenantContactType.TENANT, tenant=tenant1, contact=contact1,
                           start_date=datetime.date(year=2000, month=1, day=1))

    rent = rent_factory(
        lease=lease,
        type=RentType.FIXED,
        cycle=RentCycle.JANUARY_TO_DECEMBER,
        due_dates_type=DueDatesType.FIXED,
        due_dates_per_year=1,
    )

    contract_rent_factory(
        rent=rent,
        intended_use_id=1,
        amount=1000,
        period=PeriodType.PER_MONTH,
        base_amount=1000,
        base_amount_period=PeriodType.PER_MONTH,
    )

    if notes:
        for note in notes:
            billing_period_start_date = datetime.datetime.strptime(note['start'], '%Y%m%d').date()
            billing_period_end_date = datetime.datetime.strptime(note['end'], '%Y%m%d').date()

            invoice_note_factory(lease=lease, billing_period_start_date=billing_period_start_date,
                                 billing_period_end_date=billing_period_end_date, notes=note['notes'])

    period_rents = lease.determine_payable_rents_and_periods(datetime.date(year=2017, month=1, day=1),
                                                             datetime.date(year=2017, month=1, day=31))
    period_invoice_data = lease.calculate_invoices(period_rents)

    assert len(period_invoice_data) == 1
    assert len(period_invoice_data[0]) == 1

    invoice_data = period_invoice_data[0][0]

    assert invoice_data['notes'] == expected


@pytest.mark.django_db
def test_is_empty_empty(django_db_setup, lease_factory):
    lease = lease_factory(type_id=1, municipality_id=1, district_id=1)

    assert lease.is_empty()


@pytest.mark.django_db
def test_is_empty_one_field(django_db_setup, lease_factory):
    lease = lease_factory(type_id=1, municipality_id=1, district_id=1)
    lease.start_date = datetime.date(year=2000, month=1, day=1)

    assert not lease.is_empty()


@pytest.mark.django_db
def test_is_empty_one_foreign(django_db_setup, lease_factory, contact_factory):
    lease = lease_factory(type_id=1, municipality_id=1, district_id=1)

    contact = contact_factory(type=ContactType.OTHER, is_lessor=True)

    lease.lessor = contact

    assert not lease.is_empty()


@pytest.mark.django_db
def test_is_empty_one_relation(django_db_setup, lease_factory, decision_factory):
    lease = lease_factory(type_id=1, municipality_id=1, district_id=1)

    decision_factory(lease=lease)

    assert not lease.is_empty()


@pytest.mark.django_db
def test_is_empty_one_manytomany(django_db_setup, lease_factory, related_lease_factory):
    lease = lease_factory(type_id=1, municipality_id=1, district_id=1)
    lease2 = lease_factory(type_id=1, municipality_id=1, district_id=2)

    related_lease_factory(from_lease=lease, to_lease=lease2)

    assert not lease.is_empty()
