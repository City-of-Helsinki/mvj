import datetime
from decimal import Decimal

import pytest

from laske_export.document.invoice_sales_order_adapter import InvoiceSalesOrderAdapter
from laske_export.document.sales_order import SalesOrder
from leasing.enums import ContactType, DueDatesType, RentCycle, TenantContactType
from leasing.models import ReceivableType


@pytest.mark.django_db
def test_ponumber_from_single_tenant(django_db_setup, lease_factory, rent_factory, contact_factory, tenant_factory,
                                     tenant_rent_share_factory, tenant_contact_factory, invoice_factory,
                                     invoice_row_factory):
    lease = lease_factory(
        type_id=1,
        municipality_id=1,
        district_id=5,
        notice_period_id=1,
    )

    rent_factory(
        lease=lease,
        cycle=RentCycle.APRIL_TO_MARCH,
        due_dates_type=DueDatesType.FIXED,
        due_dates_per_year=1,
    )

    tenant1 = tenant_factory(lease=lease, share_numerator=1, share_denominator=1, reference='testreference')
    tenant_rent_share_factory(tenant=tenant1, intended_use_id=1, share_numerator=1, share_denominator=1)
    contact1 = contact_factory(first_name="First name 1", last_name="Last name 1", type=ContactType.PERSON)
    tenant_contact_factory(type=TenantContactType.TENANT, tenant=tenant1, contact=contact1,
                           start_date=datetime.date(year=2000, month=1, day=1))

    billing_period_start_date = datetime.date(year=2017, month=7, day=1)
    billing_period_end_date = datetime.date(year=2017, month=12, day=31)

    invoice = invoice_factory(
        lease=lease,
        total_amount=Decimal('123.45'),
        billed_amount=Decimal('123.45'),
        outstanding_amount=Decimal('123.45'),
        recipient=contact1,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
    )

    receivable_type = ReceivableType.objects.get(pk=1)

    invoice_row_factory(
        invoice=invoice,
        tenant=tenant1,
        receivable_type=receivable_type,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
        amount=Decimal('123.45'),
    )

    sales_order = SalesOrder()

    adapter = InvoiceSalesOrderAdapter(
        invoice=invoice,
        sales_order=sales_order,
        receivable_type_rent=receivable_type
    )

    adapter.set_values()

    assert adapter.get_po_number() == 'testreference'


@pytest.mark.django_db
def test_ponumber_from_recipient_tenant(django_db_setup, lease_factory, rent_factory, contact_factory, tenant_factory,
                                        tenant_rent_share_factory, tenant_contact_factory, invoice_factory,
                                        invoice_row_factory):
    lease = lease_factory(
        type_id=1,
        municipality_id=1,
        district_id=5,
        notice_period_id=1,
    )

    rent_factory(
        lease=lease,
        cycle=RentCycle.APRIL_TO_MARCH,
        due_dates_type=DueDatesType.FIXED,
        due_dates_per_year=1,
    )

    tenant1 = tenant_factory(lease=lease, share_numerator=1, share_denominator=2, reference='testreference1')
    tenant_rent_share_factory(tenant=tenant1, intended_use_id=1, share_numerator=1, share_denominator=2)
    contact1 = contact_factory(first_name="First name 1", last_name="Last name 1", type=ContactType.PERSON)
    tenant_contact_factory(type=TenantContactType.TENANT, tenant=tenant1, contact=contact1,
                           start_date=datetime.date(year=2000, month=1, day=1))

    tenant2 = tenant_factory(lease=lease, share_numerator=1, share_denominator=2, reference='testreference2')
    tenant_rent_share_factory(tenant=tenant2, intended_use_id=1, share_numerator=1, share_denominator=2)
    contact2 = contact_factory(first_name="First name 2", last_name="Last name 2", type=ContactType.PERSON)
    tenant_contact_factory(type=TenantContactType.TENANT, tenant=tenant2, contact=contact2,
                           start_date=datetime.date(year=2000, month=1, day=1))

    billing_period_start_date = datetime.date(year=2017, month=7, day=1)
    billing_period_end_date = datetime.date(year=2017, month=12, day=31)

    invoice = invoice_factory(
        lease=lease,
        total_amount=Decimal('200'),
        billed_amount=Decimal('200'),
        outstanding_amount=Decimal('200'),
        recipient=contact2,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
    )

    receivable_type = ReceivableType.objects.get(pk=1)

    invoice_row_factory(
        invoice=invoice,
        tenant=tenant1,
        receivable_type=receivable_type,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
        amount=Decimal('100'),
    )
    invoice_row_factory(
        invoice=invoice,
        tenant=tenant2,
        receivable_type=receivable_type,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
        amount=Decimal('100'),
    )

    sales_order = SalesOrder()

    adapter = InvoiceSalesOrderAdapter(
        invoice=invoice,
        sales_order=sales_order,
        receivable_type_rent=receivable_type
    )

    adapter.set_values()

    assert adapter.get_po_number() == 'testreference2'


@pytest.mark.django_db
def test_ponumber_from_all_tenants(django_db_setup, lease_factory, rent_factory, contact_factory, tenant_factory,
                                   tenant_rent_share_factory, tenant_contact_factory, invoice_factory,
                                   invoice_row_factory):
    lease = lease_factory(
        type_id=1,
        municipality_id=1,
        district_id=5,
        notice_period_id=1,
    )

    rent_factory(
        lease=lease,
        cycle=RentCycle.APRIL_TO_MARCH,
        due_dates_type=DueDatesType.FIXED,
        due_dates_per_year=1,
    )

    tenant1 = tenant_factory(lease=lease, share_numerator=1, share_denominator=2, reference='testreference1')
    tenant_rent_share_factory(tenant=tenant1, intended_use_id=1, share_numerator=1, share_denominator=2)
    contact1 = contact_factory(first_name="First name 1", last_name="Last name 1", type=ContactType.PERSON)
    tenant_contact_factory(type=TenantContactType.TENANT, tenant=tenant1, contact=contact1,
                           start_date=datetime.date(year=2000, month=1, day=1))

    tenant2 = tenant_factory(lease=lease, share_numerator=1, share_denominator=2, reference='testreference2')
    tenant_rent_share_factory(tenant=tenant2, intended_use_id=1, share_numerator=1, share_denominator=2)
    contact2 = contact_factory(first_name="First name 2", last_name="Last name 2", type=ContactType.PERSON)
    tenant_contact_factory(type=TenantContactType.TENANT, tenant=tenant2, contact=contact2,
                           start_date=datetime.date(year=2000, month=1, day=1))

    contact3 = contact_factory(first_name="First name 3", last_name="Last name 3", type=ContactType.PERSON)

    billing_period_start_date = datetime.date(year=2017, month=7, day=1)
    billing_period_end_date = datetime.date(year=2017, month=12, day=31)

    invoice = invoice_factory(
        lease=lease,
        total_amount=Decimal('200'),
        billed_amount=Decimal('200'),
        outstanding_amount=Decimal('200'),
        recipient=contact3,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
    )

    receivable_type = ReceivableType.objects.get(pk=1)

    invoice_row_factory(
        invoice=invoice,
        tenant=tenant1,
        receivable_type=receivable_type,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
        amount=Decimal('100'),
    )
    invoice_row_factory(
        invoice=invoice,
        tenant=tenant2,
        receivable_type=receivable_type,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
        amount=Decimal('100'),
    )

    sales_order = SalesOrder()

    adapter = InvoiceSalesOrderAdapter(
        invoice=invoice,
        sales_order=sales_order,
        receivable_type_rent=receivable_type
    )

    adapter.set_values()

    assert adapter.get_po_number() == 'testreference1 testreference2'
