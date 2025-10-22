import datetime
from decimal import Decimal

import pytest
from django.db.models.aggregates import Sum
from django.utils import timezone

from leasing.enums import (
    ContactType,
    DueDatesType,
    PeriodType,
    RentCycle,
    RentType,
    TenantContactType,
)
from leasing.models import Invoice
from leasing.models.invoice import InvoiceRow
from leasing.models.lease import Lease


@pytest.mark.django_db
def test_add_rounded_amount(
    django_db_setup,
    lease_factory,
    contact_factory,
    tenant_factory,
    tenant_contact_factory,
    tenant_rent_share_factory,
    rent_factory,
    contract_rent_factory,
):
    lease = lease_factory(
        type_id=1,
        municipality_id=1,
        district_id=1,
        notice_period_id=1,
        start_date=datetime.date(year=2000, month=1, day=1),
    )

    tenant1 = tenant_factory(lease=lease, share_numerator=1, share_denominator=2)
    contact1 = contact_factory(
        first_name="First name 1", last_name="Last name 1", type=ContactType.PERSON
    )
    tenant_contact_factory(
        type=TenantContactType.TENANT,
        tenant=tenant1,
        contact=contact1,
        start_date=datetime.date(year=2000, month=1, day=1),
    )
    tenant_rent_share_factory(
        tenant=tenant1, intended_use_id=1, share_numerator=1, share_denominator=1
    )
    tenant_rent_share_factory(
        tenant=tenant1, intended_use_id=2, share_numerator=1, share_denominator=2
    )

    tenant2 = tenant_factory(lease=lease, share_numerator=1, share_denominator=2)
    contact2 = contact_factory(
        first_name="First name 2", last_name="Last name 2", type=ContactType.PERSON
    )
    tenant_contact_factory(
        type=TenantContactType.TENANT,
        tenant=tenant2,
        contact=contact2,
        start_date=datetime.date(year=2000, month=1, day=1),
    )
    tenant_rent_share_factory(
        tenant=tenant2, intended_use_id=2, share_numerator=1, share_denominator=2
    )

    rent = rent_factory(
        lease=lease,
        type=RentType.FIXED,
        cycle=RentCycle.JANUARY_TO_DECEMBER,
        due_dates_type=DueDatesType.FIXED,
        due_dates_per_year=12,
    )
    contract_rent_factory(
        rent=rent,
        intended_use_id=1,
        amount=1000,
        period=PeriodType.PER_YEAR,
        base_amount=1000,
        base_amount_period=PeriodType.PER_YEAR,
    )
    contract_rent_factory(
        rent=rent,
        intended_use_id=2,
        amount=100,
        period=PeriodType.PER_YEAR,
        base_amount=100,
        base_amount_period=PeriodType.PER_YEAR,
    )

    rent_amount_for_year = lease.calculate_rent_amount_for_year(2017).get_total_amount()
    assert rent_amount_for_year == Decimal(1100)

    year_start = datetime.date(year=2017, month=1, day=1)
    year_end = datetime.date(year=2017, month=12, day=31)

    period_rents = lease.determine_payable_rents_and_periods(year_start, year_end)

    for period_invoice_data in lease.calculate_invoices(period_rents):
        for invoice_data in period_invoice_data:
            invoice_data.pop("explanations")
            invoice_data.pop("calculation_result")
            invoice_row_data = invoice_data.pop("rows")

            invoice_data["generated"] = True
            invoice_data["invoicing_date"] = timezone.now().date()
            invoice_data["outstanding_amount"] = invoice_data["billed_amount"]

            invoice = Invoice.objects.create(**invoice_data)

            for invoice_row_datum in invoice_row_data:
                invoice_row_datum["invoice"] = invoice
                InvoiceRow.objects.create(**invoice_row_datum)

    invoice_sum = lease.invoices.aggregate(sum=Sum("rows__amount"))["sum"]

    assert invoice_sum == rent_amount_for_year


@pytest.mark.django_db
def test_add_rounded_amount_override_receivable_type(
    django_db_setup,
    lease_factory,
    contact_factory,
    tenant_factory,
    tenant_contact_factory,
    tenant_rent_share_factory,
    rent_factory,
    contract_rent_factory,
    receivable_type_factory,
):
    """
    Ensure that rent sharing InvoiceRow's will have override_receivable_type of the rent.
    Test for MVJ-968
    """
    lease: Lease = lease_factory(
        type_id=1,
        municipality_id=1,
        district_id=1,
        notice_period_id=1,
        start_date=datetime.date(year=2024, month=1, day=1),
    )

    tenant1 = tenant_factory(lease=lease, share_numerator=1, share_denominator=2)
    contact1 = contact_factory(
        first_name="First name 1", last_name="Last name 1", type=ContactType.PERSON
    )
    tenant_contact_factory(
        type=TenantContactType.TENANT,
        tenant=tenant1,
        contact=contact1,
        start_date=datetime.date(year=2024, month=1, day=1),
    )
    tenant_rent_share_factory(
        tenant=tenant1, intended_use_id=1, share_numerator=1, share_denominator=1
    )
    tenant_rent_share_factory(
        tenant=tenant1, intended_use_id=2, share_numerator=1, share_denominator=2
    )

    tenant2 = tenant_factory(lease=lease, share_numerator=1, share_denominator=2)
    contact2 = contact_factory(
        first_name="First name 2", last_name="Last name 2", type=ContactType.PERSON
    )
    tenant_contact_factory(
        type=TenantContactType.TENANT,
        tenant=tenant2,
        contact=contact2,
        start_date=datetime.date(year=2024, month=1, day=1),
    )
    tenant_rent_share_factory(
        tenant=tenant2, intended_use_id=2, share_numerator=1, share_denominator=2
    )
    override_receivable_type = receivable_type_factory(name="Override Receivable Type")
    rent = rent_factory(
        lease=lease,
        type=RentType.FIXED,
        cycle=RentCycle.JANUARY_TO_DECEMBER,
        due_dates_type=DueDatesType.FIXED,
        due_dates_per_year=12,
        override_receivable_type=override_receivable_type,
    )
    contract_rent_factory(
        rent=rent,
        intended_use_id=1,
        amount=1000,
        period=PeriodType.PER_YEAR,
        base_amount=1000,
        base_amount_period=PeriodType.PER_YEAR,
    )
    contract_rent_factory(
        rent=rent,
        intended_use_id=2,
        amount=100,
        period=PeriodType.PER_YEAR,
        base_amount=100,
        base_amount_period=PeriodType.PER_YEAR,
    )

    year_start = datetime.date(year=2025, month=1, day=1)
    year_end = datetime.date(year=2025, month=12, day=31)

    period_rents = lease.determine_payable_rents_and_periods(year_start, year_end)

    for period_invoice_data in lease.calculate_invoices(period_rents):
        for invoice_data in period_invoice_data:
            invoice_data.pop("explanations")
            invoice_data.pop("calculation_result")
            invoice_row_data = invoice_data.pop("rows")

            invoice_data["generated"] = True
            invoice_data["invoicing_date"] = timezone.now().date()
            invoice_data["outstanding_amount"] = invoice_data["billed_amount"]

            invoice = Invoice.objects.create(**invoice_data)

            for invoice_row_datum in invoice_row_data:
                invoice_row_datum["invoice"] = invoice
                invoicerow = InvoiceRow.objects.create(**invoice_row_datum)
                # This needs to match the override_receivable_type set in rent
                assert invoicerow.receivable_type == override_receivable_type
