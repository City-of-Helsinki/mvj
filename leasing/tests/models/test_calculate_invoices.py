import datetime
from decimal import Decimal

import pytest

from leasing.calculation.result import CalculationAmount, CalculationResult
from leasing.enums import ContactType, DueDatesType, PeriodType, RentCycle, RentType, TenantContactType


@pytest.mark.django_db
def test_calculate_invoices_no_rents(django_db_setup, lease_test_data):
    lease = lease_test_data['lease']

    assert lease.calculate_invoices({}) == []


@pytest.mark.django_db
def test_calculate_invoices_one_tenant(django_db_setup, lease_factory, tenant_factory, contact_factory,
                                       tenant_contact_factory, tenant_rent_share_factory, rent_factory,
                                       contract_rent_factory):
    lease = lease_factory(type_id=1, municipality_id=1, district_id=1, notice_period_id=1,
                          start_date=datetime.date(year=2000, month=1, day=1))

    tenant1 = tenant_factory(lease=lease, share_numerator=1, share_denominator=1)
    tenant_rent_share_factory(tenant=tenant1, intended_use_id=1, share_numerator=1, share_denominator=1)
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

    contract_rent = contract_rent_factory(
        rent=rent,
        intended_use_id=1,
        amount=1000,
        period=PeriodType.PER_YEAR,
        base_amount=1000,
        base_amount_period=PeriodType.PER_YEAR,
    )

    billing_period = (datetime.date(year=2017, month=1, day=1),  datetime.date(year=2017, month=12, day=31))

    calculation_result = CalculationResult(*billing_period)
    calculation_result.add_amount(CalculationAmount(
        item=contract_rent,
        amount=Decimal(1000),
        date_range_start=billing_period[0],
        date_range_end=billing_period[1],
    ))

    period_rents = {
        billing_period: {
            'due_date': datetime.date(year=2017, month=6, day=1),
            'calculation_result': calculation_result,
        }
    }

    invoice_data = lease.calculate_invoices(period_rents)

    assert len(invoice_data) == 1
    assert len(invoice_data[0]) == 1
    assert invoice_data[0][0]['billed_amount'] == Decimal(1000)
    assert len(invoice_data[0][0]['rows']) == 1
    assert invoice_data[0][0]['rows'][0]['tenant'] == tenant1


@pytest.mark.django_db
def test_calculate_invoices_two_tenants(django_db_setup, lease_factory, tenant_factory, contact_factory,
                                        tenant_contact_factory, tenant_rent_share_factory, rent_factory,
                                        contract_rent_factory):
    lease = lease_factory(type_id=1, municipality_id=1, district_id=1, notice_period_id=1,
                          start_date=datetime.date(year=2000, month=1, day=1))

    tenant1 = tenant_factory(lease=lease, share_numerator=1, share_denominator=2)
    tenant_rent_share_factory(tenant=tenant1, intended_use_id=1, share_numerator=1, share_denominator=2)
    contact1 = contact_factory(first_name="First name 1", last_name="Last name 1", type=ContactType.PERSON)
    tenant_contact_factory(type=TenantContactType.TENANT, tenant=tenant1, contact=contact1,
                           start_date=datetime.date(year=2000, month=1, day=1))

    tenant2 = tenant_factory(lease=lease, share_numerator=1, share_denominator=2)
    tenant_rent_share_factory(tenant=tenant2, intended_use_id=1, share_numerator=1, share_denominator=2)
    contact2 = contact_factory(first_name="First name 2", last_name="Last name 2", type=ContactType.PERSON)
    tenant_contact_factory(type=TenantContactType.TENANT, tenant=tenant2, contact=contact2,
                           start_date=datetime.date(year=2000, month=1, day=1))

    rent = rent_factory(
        lease=lease,
        type=RentType.FIXED,
        cycle=RentCycle.JANUARY_TO_DECEMBER,
        due_dates_type=DueDatesType.FIXED,
        due_dates_per_year=1,
    )

    contract_rent = contract_rent_factory(
        rent=rent,
        intended_use_id=1,
        amount=1000,
        period=PeriodType.PER_YEAR,
        base_amount=1000,
        base_amount_period=PeriodType.PER_YEAR,
    )

    billing_period = (datetime.date(year=2017, month=1, day=1),  datetime.date(year=2017, month=12, day=31))

    calculation_result = CalculationResult(*billing_period)
    calculation_result.add_amount(CalculationAmount(
        item=contract_rent,
        amount=Decimal(1000),
        date_range_start=billing_period[0],
        date_range_end=billing_period[1],
    ))

    period_rents = {
        billing_period: {
            'due_date': datetime.date(year=2017, month=6, day=1),
            'calculation_result': calculation_result,
        }
    }

    invoice_data = lease.calculate_invoices(period_rents)

    assert len(invoice_data) == 1
    assert len(invoice_data[0]) == 2
    assert invoice_data[0][0]['billed_amount'] == Decimal(500)
    assert invoice_data[0][1]['billed_amount'] == Decimal(500)
    assert len(invoice_data[0][0]['rows']) == 1
    assert len(invoice_data[0][1]['rows']) == 1

    tenants = {invoice_data[0][0]['rows'][0]['tenant'], invoice_data[0][1]['rows'][0]['tenant']}
    assert tenants == {tenant1, tenant2}


@pytest.mark.django_db
def test_calculate_invoices_three_tenants(django_db_setup, assert_count_equal, lease_factory, tenant_factory,
                                          contact_factory, tenant_contact_factory, tenant_rent_share_factory,
                                          rent_factory, contract_rent_factory):
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

    rent = rent_factory(
        lease=lease,
        type=RentType.FIXED,
        cycle=RentCycle.JANUARY_TO_DECEMBER,
        due_dates_type=DueDatesType.FIXED,
        due_dates_per_year=1,
    )

    contract_rent = contract_rent_factory(
        rent=rent,
        intended_use_id=1,
        amount=1000,
        period=PeriodType.PER_YEAR,
        base_amount=1000,
        base_amount_period=PeriodType.PER_YEAR,
    )

    billing_period = (datetime.date(year=2017, month=1, day=1),  datetime.date(year=2017, month=12, day=31))

    calculation_result = CalculationResult(*billing_period)
    calculation_result.add_amount(CalculationAmount(
        item=contract_rent,
        amount=Decimal(1000),
        date_range_start=billing_period[0],
        date_range_end=billing_period[1],
    ))

    period_rents = {
        billing_period: {
            'due_date': datetime.date(year=2017, month=6, day=1),
            'calculation_result': calculation_result,
        }
    }

    invoice_data = lease.calculate_invoices(period_rents)

    assert len(invoice_data) == 1
    assert len(invoice_data[0]) == 3
    assert len(invoice_data[0][0]['rows']) == 1
    assert len(invoice_data[0][1]['rows']) == 1
    assert len(invoice_data[0][2]['rows']) == 1

    amounts = [
        invoice_data[0][0]['billed_amount'],
        invoice_data[0][1]['billed_amount'],
        invoice_data[0][2]['billed_amount']
    ]

    assert_count_equal(amounts, [Decimal('333.33'), Decimal('333.33'), Decimal('333.34')])

    tenants = {
        invoice_data[0][0]['rows'][0]['tenant'],
        invoice_data[0][1]['rows'][0]['tenant'],
        invoice_data[0][2]['rows'][0]['tenant']
    }

    assert tenants == {tenant1, tenant2, tenant3}
