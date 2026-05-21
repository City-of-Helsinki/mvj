import datetime
from decimal import Decimal
from typing import Callable
from unittest.mock import patch

import pytest
from django.core.exceptions import ValidationError
from django.db.models.aggregates import Sum
from django.utils import timezone
from rest_framework import exceptions

from leasing.enums import (
    ContactType,
    DueDatesType,
    PeriodicRentAdjustmentType,
    PeriodType,
    RentCycle,
    RentType,
    TenantContactType,
)
from leasing.management.commands.create_invoices import Command as CreateInvoicesCommand
from leasing.management.commands.create_invoices import create_invoices_for_lease
from leasing.models import (
    Invoice,
    Lease,
    OldDwellingsInHousingCompaniesPriceIndex,
    ReceivableType,
    Rent,
    RentDueDate,
)
from leasing.models.contact import Contact
from leasing.models.invoice import InvoiceRow
from leasing.models.rent import ContractRent
from leasing.models.service_unit import ServiceUnit
from leasing.models.tenant import Tenant, TenantContact, TenantRentShare


@pytest.mark.django_db
def test_lease_manager_get_by_identifier_invalid(django_db_setup, lease_test_data):
    with pytest.raises(RuntimeError) as e:
        Lease.objects.get_by_identifier("invalid")

    assert str(e.value) == 'identifier "invalid" doesn\'t match the identifier format'


@pytest.mark.django_db
def test_lease_manager_get_by_identifier_does_not_exist(
    django_db_setup, lease_test_data
):
    with pytest.raises(Lease.DoesNotExist) as e:
        Lease.objects.get_by_identifier("A1111-1")

    assert str(e.value) == "Lease matching query does not exist."


@pytest.mark.django_db
def test_lease_manager_get_by_identifier(django_db_setup, lease_factory):
    lease = lease_factory(
        type_id=1, municipality_id=1, district_id=5, notice_period_id=1
    )

    assert Lease.objects.get_by_identifier("A1104-1") == lease


@pytest.mark.django_db
def test_lease_manager_get_by_identifier_zero_padded_sequence(
    django_db_setup, lease_factory
):
    lease = lease_factory(
        type_id=1, municipality_id=1, district_id=5, notice_period_id=1
    )

    assert Lease.objects.get_by_identifier("A1104-0001") == lease


@pytest.mark.django_db
def test_lease_intended_use_service_unit_mismatch(
    django_db_setup, lease_factory, service_unit_factory, intended_use_factory
):
    service_unit_correct = service_unit_factory()
    service_unit_incorrect = service_unit_factory()
    intended_use_match = intended_use_factory(service_unit=service_unit_correct)
    intended_use_mismatch = intended_use_factory(service_unit=service_unit_incorrect)
    with pytest.raises(ValidationError):
        # Lease.service_unit and Lease.intended_use.service_unit do not match
        lease_factory(
            intended_use=intended_use_mismatch, service_unit=service_unit_correct
        )
    lease = lease_factory(
        intended_use=intended_use_match, service_unit=service_unit_correct
    )
    lease.intended_use = intended_use_mismatch
    with pytest.raises(ValidationError):

        # Lease.service_unit and Lease.intended_use.service_unit do not match
        lease.save()


@pytest.mark.django_db
def test_get_tenant_shares_for_period(
    django_db_setup,
    lease_factory,
    contact_factory,
    tenant_factory,
    tenant_contact_factory,
    assert_count_equal,
):
    """Lease with two tenants without billing contacts"""
    lease = lease_factory(
        type_id=1, municipality_id=1, district_id=1, notice_period_id=1
    )

    tenant1 = tenant_factory(lease=lease, share_numerator=1, share_denominator=2)
    tenant2 = tenant_factory(lease=lease, share_numerator=1, share_denominator=2)

    contact1 = contact_factory(
        first_name="First name 1", last_name="Last name 1", type=ContactType.PERSON
    )
    contact2 = contact_factory(
        first_name="First name 2", last_name="Last name 2", type=ContactType.PERSON
    )

    tenant_contact_factory(
        type=TenantContactType.TENANT,
        tenant=tenant1,
        contact=contact1,
        start_date=datetime.date(year=2017, month=1, day=1),
    )
    tenant_contact_factory(
        type=TenantContactType.TENANT,
        tenant=tenant2,
        contact=contact2,
        start_date=datetime.date(year=2017, month=1, day=1),
    )

    start_date = datetime.date(year=2017, month=1, day=1)
    end_date = datetime.date(year=2017, month=12, day=31)

    shares = lease.get_tenant_shares_for_period(start_date, end_date)

    assert len(shares) == 2
    assert_count_equal(shares.keys(), [contact1, contact2])
    assert shares[contact1] == {tenant1: [(start_date, end_date)]}
    assert shares[contact2] == {tenant2: [(start_date, end_date)]}


@pytest.mark.django_db
def test_get_tenant_shares_for_period_one_billing(
    django_db_setup,
    lease_factory,
    contact_factory,
    tenant_factory,
    tenant_contact_factory,
    assert_count_equal,
):
    """Lease with two tenants. Tenant2's billing contact is contact1"""
    lease = lease_factory(
        type_id=1, municipality_id=1, district_id=1, notice_period_id=1
    )

    tenant1 = tenant_factory(lease=lease, share_numerator=1, share_denominator=2)
    tenant2 = tenant_factory(lease=lease, share_numerator=1, share_denominator=2)

    contact1 = contact_factory(
        first_name="First name 1", last_name="Last name 1", type=ContactType.PERSON
    )
    contact2 = contact_factory(
        first_name="First name 2", last_name="Last name 2", type=ContactType.PERSON
    )

    tenant_contact_factory(
        type=TenantContactType.TENANT,
        tenant=tenant1,
        contact=contact1,
        start_date=datetime.date(year=2017, month=1, day=1),
    )
    tenant_contact_factory(
        type=TenantContactType.TENANT,
        tenant=tenant2,
        contact=contact2,
        start_date=datetime.date(year=2017, month=1, day=1),
    )
    tenant_contact_factory(
        type=TenantContactType.BILLING,
        tenant=tenant2,
        contact=contact1,
        start_date=datetime.date(year=2017, month=1, day=1),
    )

    start_date = datetime.date(year=2017, month=1, day=1)
    end_date = datetime.date(year=2017, month=12, day=31)

    shares = lease.get_tenant_shares_for_period(start_date, end_date)

    assert len(shares) == 1
    assert_count_equal(shares.keys(), [contact1])
    assert shares[contact1] == {
        tenant1: [(start_date, end_date)],
        tenant2: [(start_date, end_date)],
    }


@pytest.mark.django_db
def test_get_tenant_shares_for_period_change_tenant(
    django_db_setup,
    lease_factory,
    contact_factory,
    tenant_factory,
    tenant_contact_factory,
    assert_count_equal,
):
    """Lease with two tenants. Tenant2 changes to tenant3 mid-year"""
    lease = lease_factory(
        type_id=1, municipality_id=1, district_id=1, notice_period_id=1
    )

    tenant1 = tenant_factory(lease=lease, share_numerator=1, share_denominator=2)
    tenant2 = tenant_factory(lease=lease, share_numerator=1, share_denominator=2)
    tenant3 = tenant_factory(lease=lease, share_numerator=1, share_denominator=2)

    contact1 = contact_factory(
        first_name="First name 1", last_name="Last name 1", type=ContactType.PERSON
    )
    contact2 = contact_factory(
        first_name="First name 2", last_name="Last name 2", type=ContactType.PERSON
    )
    contact3 = contact_factory(
        first_name="First name 3", last_name="Last name 3", type=ContactType.PERSON
    )

    tenant_contact_factory(
        type=TenantContactType.TENANT,
        tenant=tenant1,
        contact=contact1,
        start_date=datetime.date(year=2017, month=1, day=1),
    )
    tenant_contact_factory(
        type=TenantContactType.TENANT,
        tenant=tenant2,
        contact=contact2,
        start_date=datetime.date(year=2017, month=1, day=1),
        end_date=datetime.date(year=2017, month=6, day=30),
    )
    tenant_contact_factory(
        type=TenantContactType.TENANT,
        tenant=tenant3,
        contact=contact3,
        start_date=datetime.date(year=2017, month=7, day=1),
    )

    start_date = datetime.date(year=2017, month=1, day=1)
    end_date = datetime.date(year=2017, month=12, day=31)

    shares = lease.get_tenant_shares_for_period(start_date, end_date)

    assert len(shares) == 3
    assert_count_equal(shares.keys(), [contact1, contact2, contact3])
    assert shares[contact1] == {tenant1: [(start_date, end_date)]}
    assert shares[contact2] == {
        tenant2: [(start_date, datetime.date(year=2017, month=6, day=30))]
    }
    assert shares[contact3] == {
        tenant3: [(datetime.date(year=2017, month=7, day=1), end_date)]
    }


@pytest.mark.django_db
def test_get_tenant_shares_for_period_same_billing_contact_twice(
    django_db_setup,
    lease_factory,
    contact_factory,
    tenant_factory,
    tenant_contact_factory,
    assert_count_equal,
):
    """Lease with one tenant with one billing contact twice"""
    lease = lease_factory(
        type_id=1, municipality_id=1, district_id=1, notice_period_id=1
    )

    tenant1 = tenant_factory(lease=lease, share_numerator=1, share_denominator=1)

    contact1 = contact_factory(
        first_name="First name 1", last_name="Last name 1", type=ContactType.PERSON
    )
    contact2 = contact_factory(
        first_name="First name 2", last_name="Last name 2", type=ContactType.PERSON
    )

    tenant_contact_factory(
        type=TenantContactType.TENANT,
        tenant=tenant1,
        contact=contact1,
        start_date=datetime.date(year=2017, month=1, day=1),
    )
    tenant_contact_factory(
        type=TenantContactType.BILLING,
        tenant=tenant1,
        contact=contact2,
        start_date=datetime.date(year=2017, month=1, day=1),
    )
    tenant_contact_factory(
        type=TenantContactType.BILLING,
        tenant=tenant1,
        contact=contact2,
        start_date=datetime.date(year=2015, month=1, day=1),
    )

    start_date = datetime.date(year=2017, month=1, day=1)
    end_date = datetime.date(year=2017, month=12, day=31)

    shares = lease.get_tenant_shares_for_period(start_date, end_date)

    assert len(shares) == 1
    assert_count_equal(shares.keys(), [contact2])

    assert shares[contact2] == {tenant1: [(start_date, end_date)]}


@pytest.mark.django_db
def test_get_tenant_shares_for_period_same_contact_twice(
    django_db_setup,
    lease_factory,
    contact_factory,
    tenant_factory,
    tenant_contact_factory,
    assert_count_equal,
):
    """Lease with one tenant with two active billing contacts"""
    lease = lease_factory(
        type_id=1, municipality_id=1, district_id=1, notice_period_id=1
    )

    tenant1 = tenant_factory(lease=lease, share_numerator=1, share_denominator=1)

    contact1 = contact_factory(
        first_name="First name 1", last_name="Last name 1", type=ContactType.PERSON
    )
    contact2 = contact_factory(
        first_name="First name 2", last_name="Last name 2", type=ContactType.PERSON
    )
    contact3 = contact_factory(
        first_name="First name 3", last_name="Last name 3", type=ContactType.PERSON
    )

    tenant_contact_factory(
        type=TenantContactType.TENANT,
        tenant=tenant1,
        contact=contact1,
        start_date=datetime.date(year=2017, month=1, day=1),
    )
    tenant_contact_factory(
        type=TenantContactType.BILLING,
        tenant=tenant1,
        contact=contact2,
        start_date=datetime.date(year=2000, month=1, day=1),
    )
    tenant_contact_factory(
        type=TenantContactType.BILLING,
        tenant=tenant1,
        contact=contact3,
        start_date=datetime.date(year=2015, month=1, day=1),
    )

    start_date = datetime.date(year=2017, month=1, day=1)
    end_date = datetime.date(year=2017, month=12, day=31)

    shares = lease.get_tenant_shares_for_period(start_date, end_date)

    assert len(shares) == 1
    assert_count_equal(shares.keys(), [contact3])

    assert shares[contact3] == {tenant1: [(start_date, end_date)]}


@pytest.mark.django_db
@pytest.mark.parametrize(
    "notes, expected",
    [
        ([], ""),
        # Non-matching notes
        ([{"start": "20180101", "end": "20181231", "notes": "Test note"}], ""),
        ([{"start": "20160101", "end": "20161231", "notes": "Test note"}], ""),
        (
            [
                {"start": "20180101", "end": "20181231", "notes": "Test note"},
                {"start": "20160101", "end": "20161231", "notes": "Test note"},
            ],
            "",
        ),
        # Matching notes
        ([{"start": "20170101", "end": "20171231", "notes": "Test note"}], "Test note"),
        (
            [
                {"start": "20170101", "end": "20171231", "notes": "Test note"},
                {"start": "20170101", "end": "20171231", "notes": "Test note2"},
            ],
            "Test note Test note2",
        ),
        # Matching and non-matching
        (
            [
                {"start": "20170101", "end": "20171231", "notes": "Test note"},
                {"start": "20180101", "end": "20181231", "notes": "Test note2"},
            ],
            "Test note",
        ),
        (
            [
                {"start": "20160101", "end": "20161231", "notes": "Test note"},
                {"start": "20170101", "end": "20171231", "notes": "Test note2"},
                {"start": "20170101", "end": "20171231", "notes": "Test note3"},
                {"start": "20180101", "end": "20181231", "notes": "Test note4"},
            ],
            "Test note2 Test note3",
        ),
    ],
)
def test_calculate_invoices_invoice_note(
    django_db_setup,
    lease_factory,
    contact_factory,
    tenant_factory,
    tenant_contact_factory,
    tenant_rent_share_factory,
    rent_factory,
    contract_rent_factory,
    invoice_note_factory,
    notes,
    expected,
):
    lease = lease_factory(
        type_id=1,
        municipality_id=1,
        district_id=1,
        notice_period_id=1,
        start_date=datetime.date(year=2000, month=1, day=1),
    )

    tenant1 = tenant_factory(lease=lease, share_numerator=1, share_denominator=1)
    tenant_rent_share_factory(
        tenant=tenant1, intended_use_id=1, share_numerator=1, share_denominator=1
    )

    contact1 = contact_factory(
        first_name="First name 1", last_name="Last name 1", type=ContactType.PERSON
    )
    tenant_contact_factory(
        type=TenantContactType.TENANT,
        tenant=tenant1,
        contact=contact1,
        start_date=datetime.date(year=2000, month=1, day=1),
    )

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
            billing_period_start_date = datetime.datetime.strptime(
                note["start"], "%Y%m%d"
            ).date()
            billing_period_end_date = datetime.datetime.strptime(
                note["end"], "%Y%m%d"
            ).date()

            invoice_note_factory(
                lease=lease,
                billing_period_start_date=billing_period_start_date,
                billing_period_end_date=billing_period_end_date,
                notes=note["notes"],
            )

    period_rents = lease.determine_payable_rents_and_periods(
        datetime.date(year=2017, month=1, day=1),
        datetime.date(year=2017, month=1, day=31),
    )
    period_invoice_data = lease.calculate_invoices(period_rents)

    assert len(period_invoice_data) == 1
    assert len(period_invoice_data[0]) == 1

    invoice_data = period_invoice_data[0][0]

    assert invoice_data["notes"] == expected


@pytest.mark.django_db
@pytest.mark.parametrize(
    "mock_today, expected_invoice_count, expected_due_date",
    [
        # today = Jan 1: only Q1 billing period is invoiceable (invoicing date Dec 1 <= Jan 1).
        # Configured due date Jan 2 is BEFORE today+17 (Jan 18) → clamp to today+17.
        (
            datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc),
            1,
            datetime.date(2026, 1, 18),
        ),
        # today = Mar 10: Q1 (due Jan 2) and Q2 (due Apr 1) billing periods are both invoiceable.
        # They are merged into one invoice. Max configured due date is Apr 1.
        # today+17 = Mar 27, which is BEFORE Apr 1 → use Apr 1 (the configured due date).
        (
            datetime.datetime(2026, 3, 10, tzinfo=datetime.timezone.utc),
            1,
            datetime.date(2026, 4, 1),
        ),
        # today = Apr 15: Q1+Q2 invoiceable. Max configured due date is Apr 1.
        # today+17 = May 2, which is AFTER Apr 1 → clamp to today+17.
        (
            datetime.datetime(2026, 4, 15, tzinfo=datetime.timezone.utc),
            1,
            datetime.date(2026, 5, 2),
        ),
    ],
)
def test_generate_first_invoices(
    django_db_setup,
    receivable_type_factory: Callable[..., ReceivableType],
    service_unit_factory: Callable[..., ServiceUnit],
    lease_factory: Callable[..., Lease],
    rent_factory: Callable[..., Rent],
    contract_rent_factory: Callable[..., ContractRent],
    contact_factory: Callable[..., Contact],
    tenant_factory: Callable[..., Tenant],
    tenant_contact_factory: Callable[..., TenantContact],
    tenant_rent_share_factory: Callable[..., TenantRentShare],
    mock_today,
    expected_invoice_count,
    expected_due_date,
):
    receivable_type = receivable_type_factory()
    service_unit = service_unit_factory(default_receivable_type_rent=receivable_type)
    lease = lease_factory(
        service_unit=service_unit,
        type_id=1,
        municipality_id=1,
        district_id=1,
        notice_period_id=1,
        start_date=datetime.date(year=2026, month=1, day=1),
    )

    rent = rent_factory(
        lease=lease,
        type=RentType.FIXED,
        cycle=RentCycle.JANUARY_TO_DECEMBER,
        due_dates_type=DueDatesType.FIXED,
        due_dates_per_year=4,
        start_date=datetime.date(year=2026, month=1, day=1),
    )
    contract_rent_factory(
        rent=rent,
        intended_use_id=1,
        amount=Decimal(1000),
        period=PeriodType.PER_YEAR,
        base_amount=Decimal(1000),
        base_amount_period=PeriodType.PER_YEAR,
    )
    contact = contact_factory(
        service_unit=service_unit,
        type=ContactType.BUSINESS,
        name="Company123",
        business_id="1234567-8",
    )
    tenant = tenant_factory(lease=lease, share_numerator=1, share_denominator=1)
    tenant_rent_share_factory(
        tenant=tenant, intended_use_id=1, share_numerator=1, share_denominator=1
    )
    tenant_contact_factory(
        type=TenantContactType.TENANT,
        tenant=tenant,
        contact=contact,
        start_date=datetime.date(year=2026, month=1, day=1),
    )

    with patch("django.utils.timezone.now", return_value=mock_today):
        invoices = lease.generate_first_invoices()

    assert len(invoices) == expected_invoice_count
    assert invoices[0].due_date == expected_due_date


def _create_lease_for_next_invoice_tests(
    receivable_type_factory,
    service_unit_factory,
    lease_factory,
    rent_factory,
    contract_rent_factory,
    contact_factory,
    tenant_factory,
    tenant_contact_factory,
    tenant_rent_share_factory,
    rent_due_date_factory=None,
    *,
    due_dates_type=DueDatesType.FIXED,
    due_dates_per_year=None,
    contract_amount=Decimal("1000"),
    custom_due_dates=None,
):
    receivable_type = receivable_type_factory()
    service_unit = service_unit_factory(default_receivable_type_rent=receivable_type)
    lease = lease_factory(
        service_unit=service_unit,
        type_id=1,
        municipality_id=1,
        district_id=1,
        notice_period_id=1,
        start_date=datetime.date(2026, 1, 1),
    )

    rent_kwargs = dict(
        lease=lease,
        type=RentType.FIXED,
        cycle=RentCycle.JANUARY_TO_DECEMBER,
        due_dates_type=due_dates_type,
        start_date=datetime.date(2026, 1, 1),
    )
    if due_dates_per_year is not None:
        rent_kwargs["due_dates_per_year"] = due_dates_per_year

    rent = rent_factory(**rent_kwargs)
    contract_rent_factory(
        rent=rent,
        intended_use_id=1,
        amount=contract_amount,
        period=PeriodType.PER_YEAR,
        base_amount=contract_amount,
        base_amount_period=PeriodType.PER_YEAR,
    )

    # Create RentDueDate objects for custom due dates if needed
    for month, day in custom_due_dates or []:
        rent_due_date_factory(rent=rent, month=month, day=day)

    contact = contact_factory(
        service_unit=service_unit,
        type=ContactType.BUSINESS,
        name="Company",
        business_id="1234567-8",
    )
    tenant = tenant_factory(lease=lease, share_numerator=1, share_denominator=1)
    tenant_rent_share_factory(
        tenant=tenant, intended_use_id=1, share_numerator=1, share_denominator=1
    )
    tenant_contact_factory(
        type=TenantContactType.TENANT,
        tenant=tenant,
        contact=contact,
        start_date=datetime.date(2026, 1, 1),
    )

    return lease


@pytest.mark.django_db
def test_next_invoice_quarterly_after_single_period_first_invoice(
    receivable_type_factory: Callable[..., ReceivableType],
    service_unit_factory: Callable[..., ServiceUnit],
    lease_factory: Callable[..., Lease],
    rent_factory: Callable[..., Rent],
    contract_rent_factory: Callable[..., ContractRent],
    contact_factory: Callable[..., Contact],
    tenant_factory: Callable[..., Tenant],
    tenant_contact_factory: Callable[..., TenantContact],
    tenant_rent_share_factory: Callable[..., TenantRentShare],
    rent_due_date_factory: Callable[..., RentDueDate],
):
    """
    today = Jan 1, 2026. Only Q1 qualifies for the first invoice (Q2 invoicing
    date is Mar 1, which is after Jan 1). The next regular invoice via the
    management command should be a normal Q2 invoice, unaffected by the
    generate_first_invoices change.
    """
    lease = _create_lease_for_next_invoice_tests(
        receivable_type_factory,
        service_unit_factory,
        lease_factory,
        rent_factory,
        contract_rent_factory,
        contact_factory,
        tenant_factory,
        tenant_contact_factory,
        tenant_rent_share_factory,
        rent_due_date_factory,
        due_dates_type=DueDatesType.FIXED,
        due_dates_per_year=4,
        contract_amount=Decimal("1000"),
    )

    with patch(
        "django.utils.timezone.now",
        return_value=datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc),
    ):
        first_invoices = lease.generate_first_invoices()

    assert len(first_invoices) == 1
    first_invoice = first_invoices[0]
    assert first_invoice.billing_period_start_date == datetime.date(2026, 1, 1)
    assert first_invoice.billing_period_end_date == datetime.date(2026, 3, 31)
    assert first_invoice.due_date == datetime.date(2026, 1, 18)

    created = create_invoices_for_lease(
        lease,
        invoicing_start_date=datetime.date(2026, 4, 1),
        invoicing_end_date=datetime.date(2026, 4, 30),
        invoicing_date=datetime.date(2026, 3, 1),
    )

    assert created == 1
    assert lease.invoices.count() == 2
    next_invoice = lease.invoices.order_by("-id").first()
    assert next_invoice.billing_period_start_date == datetime.date(2026, 4, 1)
    assert next_invoice.billing_period_end_date == datetime.date(2026, 6, 30)
    assert next_invoice.due_date == datetime.date(2026, 4, 1)
    assert next_invoice.billed_amount == Decimal("250.00")


@pytest.mark.django_db
def test_next_invoice_quarterly_after_merged_first_invoice(
    receivable_type_factory: Callable[..., ReceivableType],
    service_unit_factory: Callable[..., ServiceUnit],
    lease_factory: Callable[..., Lease],
    rent_factory: Callable[..., Rent],
    contract_rent_factory: Callable[..., ContractRent],
    contact_factory: Callable[..., Contact],
    tenant_factory: Callable[..., Tenant],
    tenant_contact_factory: Callable[..., TenantContact],
    tenant_rent_share_factory: Callable[..., TenantRentShare],
    rent_due_date_factory: Callable[..., RentDueDate],
):
    """
    today = Mar 10, 2026. Both Q1 and Q2 qualify for the first invoice (Q2
    invoicing date is Mar 1 ≤ Mar 10). They are merged into one invoice. The
    next regular invoice should be an independent Q3 invoice.
    """
    lease = _create_lease_for_next_invoice_tests(
        receivable_type_factory,
        service_unit_factory,
        lease_factory,
        rent_factory,
        contract_rent_factory,
        contact_factory,
        tenant_factory,
        tenant_contact_factory,
        tenant_rent_share_factory,
        rent_due_date_factory,
        due_dates_type=DueDatesType.FIXED,
        due_dates_per_year=4,
        contract_amount=Decimal("1000"),
    )

    with patch(
        "django.utils.timezone.now",
        return_value=datetime.datetime(2026, 3, 10, tzinfo=datetime.timezone.utc),
    ):
        first_invoices = lease.generate_first_invoices()

    assert len(first_invoices) == 1
    first_invoice = first_invoices[0]
    assert first_invoice.billing_period_start_date == datetime.date(2026, 1, 1)
    assert first_invoice.billing_period_end_date == datetime.date(2026, 6, 30)
    assert first_invoice.due_date == datetime.date(2026, 4, 1)

    created = create_invoices_for_lease(
        lease,
        invoicing_start_date=datetime.date(2026, 7, 1),
        invoicing_end_date=datetime.date(2026, 7, 31),
        invoicing_date=datetime.date(2026, 6, 1),
    )

    assert created == 1
    assert lease.invoices.count() == 2
    next_invoice = lease.invoices.order_by("-id").first()
    assert next_invoice.billing_period_start_date == datetime.date(2026, 7, 1)
    assert next_invoice.billing_period_end_date == datetime.date(2026, 9, 30)
    assert next_invoice.due_date == datetime.date(2026, 7, 1)
    assert next_invoice.billed_amount == Decimal("250.00")


@pytest.mark.django_db
def test_next_invoice_monthly(
    receivable_type_factory: Callable[..., ReceivableType],
    service_unit_factory: Callable[..., ServiceUnit],
    lease_factory: Callable[..., Lease],
    rent_factory: Callable[..., Rent],
    contract_rent_factory: Callable[..., ContractRent],
    contact_factory: Callable[..., Contact],
    tenant_factory: Callable[..., Tenant],
    tenant_contact_factory: Callable[..., TenantContact],
    tenant_rent_share_factory: Callable[..., TenantRentShare],
    rent_due_date_factory: Callable[..., RentDueDate],
):
    """
    today = Jan 1, 2026, monthly billing (12/year). Jan invoicing date is
    Dec 1 and Feb invoicing date is Jan 1, so both are included in the first
    invoice. The next regular invoice should be March only.
    """
    lease = _create_lease_for_next_invoice_tests(
        receivable_type_factory,
        service_unit_factory,
        lease_factory,
        rent_factory,
        contract_rent_factory,
        contact_factory,
        tenant_factory,
        tenant_contact_factory,
        tenant_rent_share_factory,
        rent_due_date_factory,
        due_dates_type=DueDatesType.FIXED,
        due_dates_per_year=12,
        contract_amount=Decimal("1200"),
    )

    with patch(
        "django.utils.timezone.now",
        return_value=datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc),
    ):
        first_invoices = lease.generate_first_invoices()

    assert len(first_invoices) == 1
    first_invoice = first_invoices[0]
    assert first_invoice.billing_period_start_date == datetime.date(2026, 1, 1)
    assert first_invoice.billing_period_end_date == datetime.date(2026, 2, 28)
    assert first_invoice.due_date == datetime.date(2026, 2, 1)

    created = create_invoices_for_lease(
        lease,
        invoicing_start_date=datetime.date(2026, 3, 1),
        invoicing_end_date=datetime.date(2026, 3, 31),
        invoicing_date=datetime.date(2026, 2, 1),
    )

    assert created == 1
    assert lease.invoices.count() == 2
    next_invoice = lease.invoices.order_by("-id").first()
    assert next_invoice.billing_period_start_date == datetime.date(2026, 3, 1)
    assert next_invoice.billing_period_end_date == datetime.date(2026, 3, 31)
    assert next_invoice.due_date == datetime.date(2026, 3, 1)
    assert next_invoice.billed_amount == Decimal("100.00")


@pytest.mark.django_db
def test_next_invoice_custom_due_dates(
    receivable_type_factory: Callable[..., ReceivableType],
    service_unit_factory: Callable[..., ServiceUnit],
    lease_factory: Callable[..., Lease],
    rent_factory: Callable[..., Rent],
    contract_rent_factory: Callable[..., ContractRent],
    contact_factory: Callable[..., Contact],
    tenant_factory: Callable[..., Tenant],
    tenant_contact_factory: Callable[..., TenantContact],
    tenant_rent_share_factory: Callable[..., TenantRentShare],
    rent_due_date_factory: Callable[..., RentDueDate],
):
    """
    today = Jan 1, 2026, semi-annual custom due dates (Feb 1 + Aug 1).
    H1 (Jan-Jun) is included in the first invoice. The next regular invoice
    should be the full H2 (Jul-Dec) at the configured due date.
    """
    lease = _create_lease_for_next_invoice_tests(
        receivable_type_factory,
        service_unit_factory,
        lease_factory,
        rent_factory,
        contract_rent_factory,
        contact_factory,
        tenant_factory,
        tenant_contact_factory,
        tenant_rent_share_factory,
        rent_due_date_factory,
        due_dates_type=DueDatesType.CUSTOM,
        contract_amount=Decimal("1200"),
        custom_due_dates=[(2, 1), (8, 1)],
    )

    with patch(
        "django.utils.timezone.now",
        return_value=datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc),
    ):
        first_invoices = lease.generate_first_invoices()

    assert len(first_invoices) == 1
    first_invoice = first_invoices[0]
    assert first_invoice.billing_period_start_date == datetime.date(2026, 1, 1)
    assert first_invoice.billing_period_end_date == datetime.date(2026, 6, 30)
    assert first_invoice.due_date == datetime.date(2026, 2, 1)

    created = create_invoices_for_lease(
        lease,
        invoicing_start_date=datetime.date(2026, 8, 1),
        invoicing_end_date=datetime.date(2026, 8, 31),
        invoicing_date=datetime.date(2026, 7, 1),
    )

    assert created == 1
    assert lease.invoices.count() == 2
    next_invoice = lease.invoices.order_by("-id").first()
    assert next_invoice.billing_period_start_date == datetime.date(2026, 7, 1)
    assert next_invoice.billing_period_end_date == datetime.date(2026, 12, 31)
    assert next_invoice.due_date == datetime.date(2026, 8, 1)
    assert next_invoice.billed_amount == Decimal("600.00")


@pytest.mark.django_db
def test_next_invoice_annual(
    receivable_type_factory: Callable[..., ReceivableType],
    service_unit_factory: Callable[..., ServiceUnit],
    lease_factory: Callable[..., Lease],
    rent_factory: Callable[..., Rent],
    contract_rent_factory: Callable[..., ContractRent],
    contact_factory: Callable[..., Contact],
    tenant_factory: Callable[..., Tenant],
    tenant_contact_factory: Callable[..., TenantContact],
    tenant_rent_share_factory: Callable[..., TenantRentShare],
    rent_due_date_factory: Callable[..., RentDueDate],
):
    """
    today = Jan 1, 2026, annual billing (1/year, due Jan 2). The first invoice
    covers the full year 2026. The next regular invoice should be the full year
    2027, proving correct year-rollover behaviour.
    """
    lease = _create_lease_for_next_invoice_tests(
        receivable_type_factory,
        service_unit_factory,
        lease_factory,
        rent_factory,
        contract_rent_factory,
        contact_factory,
        tenant_factory,
        tenant_contact_factory,
        tenant_rent_share_factory,
        rent_due_date_factory,
        due_dates_type=DueDatesType.FIXED,
        due_dates_per_year=1,
        contract_amount=Decimal("1000"),
    )

    with patch(
        "django.utils.timezone.now",
        return_value=datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc),
    ):
        first_invoices = lease.generate_first_invoices()

    assert len(first_invoices) == 1
    first_invoice = first_invoices[0]
    assert first_invoice.billing_period_start_date == datetime.date(2026, 1, 1)
    assert first_invoice.billing_period_end_date == datetime.date(2026, 12, 31)
    assert first_invoice.due_date == datetime.date(2026, 1, 18)

    created = create_invoices_for_lease(
        lease,
        invoicing_start_date=datetime.date(2027, 1, 1),
        invoicing_end_date=datetime.date(2027, 1, 31),
        invoicing_date=datetime.date(2026, 12, 1),
    )

    assert created == 1
    assert lease.invoices.count() == 2
    next_invoice = lease.invoices.order_by("-id").first()
    assert next_invoice.billing_period_start_date == datetime.date(2027, 1, 1)
    assert next_invoice.billing_period_end_date == datetime.date(2027, 12, 31)
    assert next_invoice.due_date == datetime.date(2027, 1, 2)
    assert next_invoice.billed_amount == Decimal("1000.00")


@pytest.mark.django_db
def test_next_invoice_create_invoices_is_idempotent(
    receivable_type_factory: Callable[..., ReceivableType],
    service_unit_factory: Callable[..., ServiceUnit],
    lease_factory: Callable[..., Lease],
    rent_factory: Callable[..., Rent],
    contract_rent_factory: Callable[..., ContractRent],
    contact_factory: Callable[..., Contact],
    tenant_factory: Callable[..., Tenant],
    tenant_contact_factory: Callable[..., TenantContact],
    tenant_rent_share_factory: Callable[..., TenantRentShare],
):
    """
    Calling create_invoices_for_lease twice with identical parameters must
    create exactly one invoice on the first call and zero on the second.
    """
    receivable_type = receivable_type_factory()
    service_unit = service_unit_factory(default_receivable_type_rent=receivable_type)
    lease = lease_factory(
        service_unit=service_unit,
        type_id=1,
        municipality_id=1,
        district_id=1,
        notice_period_id=1,
        start_date=datetime.date(2026, 1, 1),
    )
    rent = rent_factory(
        lease=lease,
        type=RentType.FIXED,
        cycle=RentCycle.JANUARY_TO_DECEMBER,
        due_dates_type=DueDatesType.FIXED,
        due_dates_per_year=4,
        start_date=datetime.date(2026, 1, 1),
    )
    contract_rent_factory(
        rent=rent,
        intended_use_id=1,
        amount=Decimal("1000"),
        period=PeriodType.PER_YEAR,
        base_amount=Decimal("1000"),
        base_amount_period=PeriodType.PER_YEAR,
    )
    contact = contact_factory(
        service_unit=service_unit,
        type=ContactType.BUSINESS,
        name="Company",
        business_id="1234567-8",
    )
    tenant = tenant_factory(lease=lease, share_numerator=1, share_denominator=1)
    tenant_rent_share_factory(
        tenant=tenant, intended_use_id=1, share_numerator=1, share_denominator=1
    )
    tenant_contact_factory(
        type=TenantContactType.TENANT,
        tenant=tenant,
        contact=contact,
        start_date=datetime.date(2026, 1, 1),
    )

    with patch(
        "django.utils.timezone.now",
        return_value=datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc),
    ):
        first_invoices = lease.generate_first_invoices()

    assert len(first_invoices) == 1

    kwargs = dict(
        lease=lease,
        invoicing_start_date=datetime.date(2026, 4, 1),
        invoicing_end_date=datetime.date(2026, 4, 30),
        invoicing_date=datetime.date(2026, 3, 1),
    )
    assert lease.invoices.count() == 1
    assert create_invoices_for_lease(**kwargs) == 1
    assert lease.invoices.count() == 2
    assert create_invoices_for_lease(**kwargs) == 0
    assert lease.invoices.count() == 2


@pytest.mark.django_db
def test_create_invoices_for_lease_creates_same_period_invoices_for_multiple_tenants(
    receivable_type_factory: Callable[..., ReceivableType],
    service_unit_factory: Callable[..., ServiceUnit],
    lease_factory: Callable[..., Lease],
    rent_factory: Callable[..., Rent],
    contract_rent_factory: Callable[..., ContractRent],
    contact_factory: Callable[..., Contact],
    tenant_factory: Callable[..., Tenant],
    tenant_contact_factory: Callable[..., TenantContact],
    tenant_rent_share_factory: Callable[..., TenantRentShare],
):
    """
    A single lease and billing period can legitimately produce multiple
    invoices when different tenants have different billing contacts.
    """
    receivable_type = receivable_type_factory()
    service_unit = service_unit_factory(default_receivable_type_rent=receivable_type)
    lease = lease_factory(
        service_unit=service_unit,
        type_id=1,
        municipality_id=1,
        district_id=1,
        notice_period_id=1,
        start_date=datetime.date(2026, 1, 1),
    )
    rent = rent_factory(
        lease=lease,
        type=RentType.FIXED,
        cycle=RentCycle.JANUARY_TO_DECEMBER,
        due_dates_type=DueDatesType.FIXED,
        due_dates_per_year=1,
        start_date=datetime.date(2026, 1, 1),
    )
    contract_rent_factory(
        rent=rent,
        intended_use_id=1,
        amount=Decimal("1000"),
        period=PeriodType.PER_YEAR,
        base_amount=Decimal("1000"),
        base_amount_period=PeriodType.PER_YEAR,
    )

    tenant1 = tenant_factory(lease=lease, share_numerator=1, share_denominator=2)
    tenant_rent_share_factory(
        tenant=tenant1, intended_use_id=1, share_numerator=1, share_denominator=2
    )
    contact1 = contact_factory(
        service_unit=service_unit,
        type=ContactType.PERSON,
        first_name="First",
        last_name="Tenant",
    )
    tenant_contact_factory(
        type=TenantContactType.TENANT,
        tenant=tenant1,
        contact=contact1,
        start_date=datetime.date(2026, 1, 1),
    )

    tenant2 = tenant_factory(lease=lease, share_numerator=1, share_denominator=2)
    tenant_rent_share_factory(
        tenant=tenant2, intended_use_id=1, share_numerator=1, share_denominator=2
    )
    contact2 = contact_factory(
        service_unit=service_unit,
        type=ContactType.PERSON,
        first_name="Second",
        last_name="Tenant",
    )
    tenant_contact_factory(
        type=TenantContactType.TENANT,
        tenant=tenant2,
        contact=contact2,
        start_date=datetime.date(2026, 1, 1),
    )

    created = create_invoices_for_lease(
        lease,
        invoicing_start_date=datetime.date(2026, 1, 1),
        invoicing_end_date=datetime.date(2026, 1, 31),
        invoicing_date=datetime.date(2025, 12, 1),
    )

    assert created == 2
    assert lease.invoices.count() == 2

    invoices = list(lease.invoices.order_by("id"))
    assert {invoice.recipient for invoice in invoices} == {contact1, contact2}
    assert {
        (
            invoice.billing_period_start_date,
            invoice.billing_period_end_date,
            invoice.billed_amount,
        )
        for invoice in invoices
    } == {(datetime.date(2026, 1, 1), datetime.date(2026, 12, 31), Decimal("500.00"))}


def _create_quarterly_lease_for_duplicate_invoice_tests(
    receivable_type_factory: Callable[..., ReceivableType],
    service_unit_factory: Callable[..., ServiceUnit],
    lease_factory: Callable[..., Lease],
    rent_factory: Callable[..., Rent],
    contract_rent_factory: Callable[..., ContractRent],
    contact_factory: Callable[..., Contact],
    tenant_factory: Callable[..., Tenant],
    tenant_contact_factory: Callable[..., TenantContact],
    tenant_rent_share_factory: Callable[..., TenantRentShare],
) -> Lease:
    receivable_type = receivable_type_factory()
    service_unit = service_unit_factory(default_receivable_type_rent=receivable_type)
    lease = lease_factory(
        service_unit=service_unit,
        type_id=1,
        municipality_id=1,
        district_id=1,
        notice_period_id=1,
        start_date=datetime.date(2026, 1, 1),
    )
    rent = rent_factory(
        lease=lease,
        type=RentType.FIXED,
        cycle=RentCycle.JANUARY_TO_DECEMBER,
        due_dates_type=DueDatesType.FIXED,
        due_dates_per_year=4,
        start_date=datetime.date(2026, 1, 1),
    )
    contract_rent_factory(
        rent=rent,
        intended_use_id=1,
        amount=Decimal("1000"),
        period=PeriodType.PER_YEAR,
        base_amount=Decimal("1000"),
        base_amount_period=PeriodType.PER_YEAR,
    )
    contact = contact_factory(
        service_unit=service_unit,
        type=ContactType.BUSINESS,
        name="Company",
        business_id="1234567-8",
    )
    tenant = tenant_factory(lease=lease, share_numerator=1, share_denominator=1)
    tenant_rent_share_factory(
        tenant=tenant, intended_use_id=1, share_numerator=1, share_denominator=1
    )
    tenant_contact_factory(
        type=TenantContactType.TENANT,
        tenant=tenant,
        contact=contact,
        start_date=datetime.date(2026, 1, 1),
    )

    return lease


@pytest.mark.django_db
@pytest.mark.xfail(
    reason="Temporarily expected to fail after partial revert of ad4c8e17"
)
def test_direct_q2_overlap_is_not_double_invoiced_after_merged_first_invoice(
    receivable_type_factory: Callable[..., ReceivableType],
    service_unit_factory: Callable[..., ServiceUnit],
    lease_factory: Callable[..., Lease],
    rent_factory: Callable[..., Rent],
    contract_rent_factory: Callable[..., ContractRent],
    contact_factory: Callable[..., Contact],
    tenant_factory: Callable[..., Tenant],
    tenant_contact_factory: Callable[..., TenantContact],
    tenant_rent_share_factory: Callable[..., TenantRentShare],
):
    """
    today = Mar 1, 2026. generate_first_invoices merges Q1 and Q2 into a single
    invoice (billing_period Jan 1-Jun 30, due Apr 1). On the same day the
    management command would run to invoice the Q2 due date, targeting the
    window Apr 1-Apr 30. Since the merged first invoice has a different
    billing_period_start_date (Jan 1 vs Apr 1), the duplicate-check in
    create_invoices_for_lease does not detect the overlap and may create a
    second invoice for Q2 (Apr 1-Jun 30), double-billing the tenant.

    The desired behaviour is zero new invoices created (returns 0).
    """
    lease = _create_quarterly_lease_for_duplicate_invoice_tests(
        receivable_type_factory,
        service_unit_factory,
        lease_factory,
        rent_factory,
        contract_rent_factory,
        contact_factory,
        tenant_factory,
        tenant_contact_factory,
        tenant_rent_share_factory,
    )

    # today = Mar 1: Q1 (invoicing_date Dec 1) and Q2 (invoicing_date Mar 1)
    # both ≤ Mar 1 → both included and merged.
    with patch(
        "django.utils.timezone.now",
        return_value=datetime.datetime(2026, 3, 1, tzinfo=datetime.timezone.utc),
    ):
        first_invoices = lease.generate_first_invoices()

    assert len(first_invoices) == 1
    assert first_invoices[0].billing_period_start_date == datetime.date(2026, 1, 1)
    assert first_invoices[0].billing_period_end_date == datetime.date(2026, 6, 30)

    # The management command runs on the same day, targeting the Apr 1 due-date
    # window. The desired result is 0 (no duplicate). Currently returns 1 (bug).
    created = create_invoices_for_lease(
        lease,
        invoicing_start_date=datetime.date(2026, 4, 1),
        invoicing_end_date=datetime.date(2026, 4, 30),
        invoicing_date=datetime.date(2026, 3, 1),
    )

    assert created == 0, (
        f"Expected 0 invoices created (Q2 already covered by merged first invoice), "
        f"but got {created}. This is a duplicate billing bug."
    )


@pytest.mark.django_db
# @pytest.mark.xfail(
#     reason="Temporarily expected to fail after partial revert of ad4c8e17"
# )
def test_regular_command_after_april_enablement_does_not_duplicate_merged_invoice_period(
    receivable_type_factory: Callable[..., ReceivableType],
    service_unit_factory: Callable[..., ServiceUnit],
    lease_factory: Callable[..., Lease],
    rent_factory: Callable[..., Rent],
    contract_rent_factory: Callable[..., ContractRent],
    contact_factory: Callable[..., Contact],
    tenant_factory: Callable[..., Tenant],
    tenant_contact_factory: Callable[..., TenantContact],
    tenant_rent_share_factory: Callable[..., TenantRentShare],
):
    """
    Proves that the automated management command cannot create a duplicate
    invoice for a period already covered by the merged first invoice.

    Scenario:
    - Invoicing enabled Apr 1, 2026: set_invoicing_enabled calls
      generate_first_invoices, which merges Q1 and Q2 into a single invoice
      (billing_period Jan 1-Jun 30, due Apr 1).
    - The command's one-month lookahead means it never targets the Apr 1 window
      after the lease is already enabled. The first command run that finds a
      due date for this lease is Jun 1, targeting Jul 1-31 (Q3 due date Jul 1).
    - Q3 invoice (Jul 1-Sep 30, due Jul 1, 250.00) is created normally.
    - Total invoices = 2; the merged Q1+Q2 invoice is untouched.

    The Apr→Jun gap is the structural reason the automated command is safe:
    by the time invoicing is enabled (Apr 1), the Apr 1 window has already
    passed (command ran Mar 1) and the next run (May 1) targets May 1-31
    where no quarterly due date falls.
    """
    lease = _create_quarterly_lease_for_duplicate_invoice_tests(
        receivable_type_factory,
        service_unit_factory,
        lease_factory,
        rent_factory,
        contract_rent_factory,
        contact_factory,
        tenant_factory,
        tenant_contact_factory,
        tenant_rent_share_factory,
    )

    # today = Apr 1: Q1 (invoicing_date Dec 1) and Q2 (invoicing_date Mar 1)
    # both ≤ Apr 1 → merged into one invoice (Jan 1-Jun 30, due Apr 1).
    # Q3 invoicing_date Jun 1 > Apr 1 → excluded from first invoice.
    # set_invoicing_enabled also sets invoicing_enabled_at so the command
    # queryset can find this lease.
    with patch(
        "django.utils.timezone.now",
        return_value=datetime.datetime(2026, 4, 1, tzinfo=datetime.timezone.utc),
    ):
        lease.set_invoicing_enabled(True)

    assert lease.invoices.count() == 1
    merged_invoice = lease.invoices.first()
    assert merged_invoice.billing_period_start_date == datetime.date(2026, 1, 1)
    assert merged_invoice.billing_period_end_date == datetime.date(2026, 6, 30)
    assert merged_invoice.due_date == datetime.date(
        2026, 4, 18
    )  # max(Apr 1, today+17=Apr 18) = Apr 18
    assert merged_invoice.billed_amount == Decimal("500.00")  # Q1+Q2 = 250+250

    # Command runs Jun 1: start_of_next_month=Jul 1, end_of_next_month=Jul 31.
    # Finds Q3 due date Jul 1 → billing period Jul 1-Sep 30. The merged
    # Q1+Q2 invoice (Jan 1-Jun 30) is not targeted by this window at all.

    with patch(
        "django.utils.timezone.now",
        return_value=datetime.datetime(2026, 6, 1, tzinfo=datetime.timezone.utc),
    ):
        CreateInvoicesCommand().handle()

    assert lease.invoices.count() == 2
    q3_invoice = lease.invoices.order_by("-id").first()
    assert q3_invoice.billing_period_start_date == datetime.date(2026, 7, 1)
    assert q3_invoice.billing_period_end_date == datetime.date(2026, 9, 30)
    assert q3_invoice.due_date == datetime.date(2026, 7, 1)
    assert q3_invoice.billed_amount == Decimal("250.00")

    # The merged first invoice is untouched.
    merged_invoice.refresh_from_db()
    assert merged_invoice.billing_period_start_date == datetime.date(2026, 1, 1)
    assert merged_invoice.billing_period_end_date == datetime.date(2026, 6, 30)


@pytest.mark.django_db
@pytest.mark.xfail(
    reason="Temporarily expected to fail after partial revert of ad4c8e17"
)
@pytest.mark.parametrize(
    "create_invoices_current_date, use_override",
    [
        pytest.param(
            datetime.datetime(2026, 6, 1, tzinfo=datetime.timezone.utc),
            False,
            id="scheduled-run-on-june-1",
        ),
        pytest.param(
            datetime.datetime(2026, 6, 2, tzinfo=datetime.timezone.utc),
            True,
            id="forced-run-on-june-2",
        ),
    ],
)
def test_same_day_june_enablement_does_not_double_invoice_q3(
    receivable_type_factory: Callable[..., ReceivableType],
    service_unit_factory: Callable[..., ServiceUnit],
    lease_factory: Callable[..., Lease],
    rent_factory: Callable[..., Rent],
    contract_rent_factory: Callable[..., ContractRent],
    contact_factory: Callable[..., Contact],
    tenant_factory: Callable[..., Tenant],
    tenant_contact_factory: Callable[..., TenantContact],
    tenant_rent_share_factory: Callable[..., TenantRentShare],
    create_invoices_current_date: datetime.datetime,
    use_override: bool,
):
    """
    Desired behaviour for a same-day Jun 1 edge case: the automated monthly
    command must not create a duplicate invoice for Q3 when invoicing was
    enabled earlier that same day and the merged first invoice already covers
    Jan 1-Sep 30.

    Scenario:
    - Invoicing is enabled on Jun 1, 2026.
    - set_invoicing_enabled calls generate_first_invoices, which includes Q1,
      Q2, and Q3 and merges them into one invoice
      (billing_period Jan 1-Sep 30, due Jul 1).
    - Later on the same day, the monthly create_invoices command runs.
      Its one-month lookahead targets Jul 1-Jul 31, which maps to the Q3
      billing period Jul 1-Sep 30.

    The desired result is still a single invoice, because Q3 is already covered
    by the merged first invoice. This test is expected to fail until the
    duplicate detection handles overlapping billing periods rather than exact
    billing-period boundaries only.
    """
    lease = _create_quarterly_lease_for_duplicate_invoice_tests(
        receivable_type_factory,
        service_unit_factory,
        lease_factory,
        rent_factory,
        contract_rent_factory,
        contact_factory,
        tenant_factory,
        tenant_contact_factory,
        tenant_rent_share_factory,
    )

    # today = Jun 1: Q1 (invoicing_date Dec 1), Q2 (Mar 1), and Q3 (Jun 1)
    # all satisfy invoicing_date ≤ today, so generate_first_invoices merges
    # them into a single Jan 1-Sep 30 invoice. set_invoicing_enabled also sets
    # invoicing_enabled_at so the monthly command queryset can find this lease.
    with patch(
        "django.utils.timezone.now",
        return_value=datetime.datetime(2026, 6, 1, tzinfo=datetime.timezone.utc),
    ):
        lease.set_invoicing_enabled(True)

    assert lease.invoices.count() == 1, (
        "Expected the Jun 1 monthly command not to create a duplicate Q3 invoice, "
        "because the merged first invoice already covers Jan 1-Sep 30."
    )
    merged_invoice = lease.invoices.first()
    assert merged_invoice.billing_period_start_date == datetime.date(2026, 1, 1)
    assert merged_invoice.billing_period_end_date == datetime.date(2026, 9, 30)
    assert merged_invoice.due_date == datetime.date(
        2026, 7, 1
    )  # max(Jul 1, today+17=Jun 18) = Jul 1
    assert merged_invoice.billed_amount == Decimal("750.00")  # Q1+Q2+Q3 = 250*3

    # Command runs Jun 1: start_of_next_month=Jul 1, end_of_next_month=Jul 31.
    # Finds Q3 due date Jul 1 → billing period Jul 1-Sep 30. That period is
    # already covered by the merged Jan 1-Sep 30 invoice, so the desired
    # outcome is still exactly one invoice.

    with patch(
        "django.utils.timezone.now",
        return_value=create_invoices_current_date,
    ):
        if use_override:
            CreateInvoicesCommand().handle(override=True)
        else:
            CreateInvoicesCommand().handle()

    # New invoice should not be created, because the Q3 billing period (Jul 1-Sep 30)
    # is already covered by the merged first invoice (Jan 1-Sep 30).
    assert lease.invoices.count() == 1

    # The merged first invoice is untouched.
    merged_invoice.refresh_from_db()
    assert merged_invoice.billing_period_start_date == datetime.date(2026, 1, 1)
    assert merged_invoice.billing_period_end_date == datetime.date(2026, 9, 30)
    assert merged_invoice.due_date == datetime.date(2026, 7, 1)
    assert merged_invoice.billed_amount == Decimal("750.00")


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


@pytest.mark.django_db
def test_add_rounded_amount(
    django_db_setup,
    lease_factory,
    contact_factory,
    tenant_factory,
    tenant_contact_factory,
    invoice_factory,
    invoice_row_factory,
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

    tenant1 = tenant_factory(lease=lease, share_numerator=1, share_denominator=1)

    contact1 = contact_factory(
        first_name="First name 1", last_name="Last name 1", type=ContactType.PERSON
    )

    tenant_contact_factory(
        type=TenantContactType.TENANT,
        tenant=tenant1,
        contact=contact1,
        start_date=datetime.date(year=2000, month=1, day=1),
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

    assert lease.calculate_rent_amount_for_year(2017).get_total_amount() == Decimal(
        1000
    )

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

    assert invoice_sum == lease.calculate_rent_amount_for_year(2017).get_total_amount()


@pytest.mark.django_db
def test_add_rounded_amount_previous_invoices(
    django_db_setup,
    lease_factory,
    contact_factory,
    tenant_factory,
    tenant_contact_factory,
    invoice_factory,
    invoice_row_factory,
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

    tenant1 = tenant_factory(lease=lease, share_numerator=1, share_denominator=1)

    contact1 = contact_factory(
        first_name="First name 1", last_name="Last name 1", type=ContactType.PERSON
    )

    tenant_contact_factory(
        type=TenantContactType.TENANT,
        tenant=tenant1,
        contact=contact1,
        start_date=datetime.date(year=2000, month=1, day=1),
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

    assert lease.calculate_rent_amount_for_year(2017).get_total_amount() == Decimal(
        1000
    )

    year_start = datetime.date(year=2017, month=1, day=1)
    end_of_june = datetime.date(year=2017, month=6, day=30)
    start_of_july = datetime.date(year=2017, month=7, day=1)
    year_end = datetime.date(year=2017, month=12, day=31)

    # Generate invoices for the first half of the year
    period_rents = lease.determine_payable_rents_and_periods(year_start, end_of_june)

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

    # Add an invoice with a non-rent row (This shouldn't affect the rounding error calculation)
    invoice = invoice_factory(
        lease=lease,
        total_amount=Decimal(100),
        billed_amount=Decimal(100),
        outstanding_amount=Decimal(100),
        recipient=contact1,
        billing_period_start_date=datetime.date(year=2017, month=1, day=1),
        billing_period_end_date=datetime.date(year=2017, month=1, day=31),
        generated=True,
    )

    receivable_type2 = ReceivableType.objects.get(pk=2)

    invoice_row_factory(
        invoice=invoice,
        tenant=tenant1,
        receivable_type=receivable_type2,
        billing_period_start_date=datetime.date(year=2017, month=1, day=1),
        billing_period_end_date=datetime.date(year=2017, month=1, day=31),
        amount=Decimal(100),
    )

    # Add rest of the invoices
    period_rents = lease.determine_payable_rents_and_periods(start_of_july, year_end)

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

    invoice_sum = InvoiceRow.objects.filter(
        invoice__in=Invoice.objects.filter(lease=lease), receivable_type_id=1
    ).aggregate(sum=Sum("amount"))["sum"]

    assert invoice_sum == lease.calculate_rent_amount_for_year(2017).get_total_amount()


@pytest.mark.django_db
def test_lease_validate_rents(
    lease_factory: Callable[..., Lease],
    rent_factory: Callable[..., Rent],
    rent_due_date_factory: Callable[..., RentDueDate],
    old_dwellings_in_housing_companies_price_index_factory: Callable[
        ..., OldDwellingsInHousingCompaniesPriceIndex
    ],
    receivable_type_factory: Callable[..., ReceivableType],
    service_unit_factory: Callable[..., ServiceUnit],
):
    """
    Tests lease.validate_rents().

    Focus is to ensure that this function is in line with
    leasing.serializers.rent.RentCreateUpdateSerializer.validate()
    """
    service_unit = service_unit_factory(use_rent_override_receivable_type=True)
    lease = lease_factory(service_unit=service_unit)

    # Happy path with correct variables
    index = old_dwellings_in_housing_companies_price_index_factory()
    receivable_type = receivable_type_factory()
    valid_rent = rent_factory(
        lease=lease,
        old_dwellings_in_housing_companies_price_index=index,
        periodic_rent_adjustment_type=PeriodicRentAdjustmentType.TASOTARKISTUS_20_10,
        type=RentType.FIXED,
        override_receivable_type=receivable_type,
    )
    rent_due_date_factory.create_batch(12, rent=valid_rent, day=1, month=1)
    assert lease.validate_rents() is None

    # Fail due to wrong number of custom due dates in the rent
    invalid_rent = rent_factory(lease=lease)
    rent_due_date_factory.create_batch(7, rent=invalid_rent, day=1, month=1)
    with pytest.raises(exceptions.ValidationError):
        lease.validate_rents()

    # Reset to valid
    invalid_rent.delete()
    assert lease.validate_rents() is None

    # Fail due to missing rent.periodic_rent_adjustment_type
    invalid_rent = rent_factory(
        lease=lease, old_dwellings_in_housing_companies_price_index=index
    )
    with pytest.raises(exceptions.ValidationError):
        lease.validate_rents()

    # Reset to valid
    invalid_rent.delete()
    assert lease.validate_rents() is None

    # Fail due to missing rent.override_receivable_type
    invalid_rent = rent_factory(
        lease=lease,
        type=RentType.FIXED,
        override_receivable_type=None,
    )
    with pytest.raises(exceptions.ValidationError):
        lease.validate_rents()
