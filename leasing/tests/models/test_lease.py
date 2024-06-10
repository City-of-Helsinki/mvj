import datetime
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.db.models.aggregates import Sum

from leasing.enums import (
    ContactType,
    DueDatesType,
    PeriodType,
    RentCycle,
    RentType,
    TenantContactType,
)
from leasing.models import Invoice, Lease, ReceivableType
from leasing.models.invoice import InvoiceRow


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
            invoice_data["invoicing_date"] = datetime.date.today()
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
            invoice_data["invoicing_date"] = datetime.date.today()
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
            invoice_data["invoicing_date"] = datetime.date.today()
            invoice_data["outstanding_amount"] = invoice_data["billed_amount"]

            invoice = Invoice.objects.create(**invoice_data)

            for invoice_row_datum in invoice_row_data:
                invoice_row_datum["invoice"] = invoice
                InvoiceRow.objects.create(**invoice_row_datum)

    invoice_sum = InvoiceRow.objects.filter(
        invoice__in=Invoice.objects.filter(lease=lease), receivable_type_id=1
    ).aggregate(sum=Sum("amount"))["sum"]

    assert invoice_sum == lease.calculate_rent_amount_for_year(2017).get_total_amount()
