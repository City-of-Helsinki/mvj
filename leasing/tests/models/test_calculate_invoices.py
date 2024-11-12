from datetime import date
from decimal import Decimal

import pytest
from dateutil.relativedelta import relativedelta
from dateutil.rrule import MONTHLY, rrule

from leasing.calculation.result import CalculationAmount, CalculationResult
from leasing.enums import (
    ContactType,
    DueDatesType,
    PeriodType,
    RentCycle,
    RentType,
    TenantContactType,
)
from leasing.models import Lease, Rent, RentDueDate
from leasing.models.types import PayableRentsInPeriods


@pytest.mark.django_db
def test_calculate_invoices_no_rents(django_db_setup, lease_test_data):
    lease = lease_test_data["lease"]

    assert lease.calculate_invoices({}) == []


@pytest.mark.django_db
def test_calculate_invoices_one_tenant(
    django_db_setup,
    lease_factory,
    tenant_factory,
    contact_factory,
    tenant_contact_factory,
    tenant_rent_share_factory,
    rent_factory,
    contract_rent_factory,
):
    lease: Lease = lease_factory(
        type_id=1,
        municipality_id=1,
        district_id=1,
        notice_period_id=1,
        start_date=date(year=2000, month=1, day=1),
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
        start_date=date(year=2000, month=1, day=1),
    )

    rent: Rent = rent_factory(
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

    billing_period = (
        date(year=2017, month=1, day=1),
        date(year=2017, month=12, day=31),
    )

    calculation_result = CalculationResult(*billing_period)
    calculation_result.add_amount(
        CalculationAmount(
            item=contract_rent,
            amount=Decimal(1000),
            date_range_start=billing_period[0],
            date_range_end=billing_period[1],
        )
    )

    period_rents: PayableRentsInPeriods = {
        billing_period: {
            "due_date": date(year=2017, month=6, day=1),
            "calculation_result": calculation_result,
            "last_billing_period": False,
            "override_receivable_type": rent.get_override_receivable_type(),
        }
    }

    invoice_data = lease.calculate_invoices(period_rents)

    assert len(invoice_data) == 1
    assert len(invoice_data[0]) == 1
    assert invoice_data[0][0]["billed_amount"] == Decimal(1000)
    assert len(invoice_data[0][0]["rows"]) == 1
    assert invoice_data[0][0]["rows"][0]["tenant"] == tenant1


@pytest.mark.django_db
def test_calculate_invoices_two_tenants(
    django_db_setup,
    lease_factory,
    tenant_factory,
    contact_factory,
    tenant_contact_factory,
    tenant_rent_share_factory,
    rent_factory,
    contract_rent_factory,
):
    lease: Lease = lease_factory(
        type_id=1,
        municipality_id=1,
        district_id=1,
        notice_period_id=1,
        start_date=date(year=2000, month=1, day=1),
    )

    tenant1 = tenant_factory(lease=lease, share_numerator=1, share_denominator=2)
    tenant_rent_share_factory(
        tenant=tenant1, intended_use_id=1, share_numerator=1, share_denominator=2
    )
    contact1 = contact_factory(
        first_name="First name 1", last_name="Last name 1", type=ContactType.PERSON
    )
    tenant_contact_factory(
        type=TenantContactType.TENANT,
        tenant=tenant1,
        contact=contact1,
        start_date=date(year=2000, month=1, day=1),
    )

    tenant2 = tenant_factory(lease=lease, share_numerator=1, share_denominator=2)
    tenant_rent_share_factory(
        tenant=tenant2, intended_use_id=1, share_numerator=1, share_denominator=2
    )
    contact2 = contact_factory(
        first_name="First name 2", last_name="Last name 2", type=ContactType.PERSON
    )
    tenant_contact_factory(
        type=TenantContactType.TENANT,
        tenant=tenant2,
        contact=contact2,
        start_date=date(year=2000, month=1, day=1),
    )

    rent: Rent = rent_factory(
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

    billing_period = (
        date(year=2017, month=1, day=1),
        date(year=2017, month=12, day=31),
    )

    calculation_result = CalculationResult(*billing_period)
    calculation_result.add_amount(
        CalculationAmount(
            item=contract_rent,
            amount=Decimal(1000),
            date_range_start=billing_period[0],
            date_range_end=billing_period[1],
        )
    )

    period_rents: PayableRentsInPeriods = {
        billing_period: {
            "due_date": date(year=2017, month=6, day=1),
            "calculation_result": calculation_result,
            "last_billing_period": False,
            "override_receivable_type": rent.get_override_receivable_type(),
        }
    }

    invoice_data = lease.calculate_invoices(period_rents)

    assert len(invoice_data) == 1
    assert len(invoice_data[0]) == 2
    assert invoice_data[0][0]["billed_amount"] == Decimal(500)
    assert invoice_data[0][1]["billed_amount"] == Decimal(500)
    assert len(invoice_data[0][0]["rows"]) == 1
    assert len(invoice_data[0][1]["rows"]) == 1

    tenants = {
        invoice_data[0][0]["rows"][0]["tenant"],
        invoice_data[0][1]["rows"][0]["tenant"],
    }
    assert tenants == {tenant1, tenant2}


@pytest.mark.django_db
def test_calculate_invoices_three_tenants(
    django_db_setup,
    assert_count_equal,
    lease_factory,
    tenant_factory,
    contact_factory,
    tenant_contact_factory,
    tenant_rent_share_factory,
    rent_factory,
    contract_rent_factory,
):
    lease: Lease = lease_factory(
        type_id=1,
        municipality_id=1,
        district_id=1,
        notice_period_id=1,
        start_date=date(year=2000, month=1, day=1),
    )

    tenant1 = tenant_factory(lease=lease, share_numerator=1, share_denominator=3)
    tenant_rent_share_factory(
        tenant=tenant1, intended_use_id=1, share_numerator=1, share_denominator=3
    )
    contact1 = contact_factory(
        first_name="First name 1", last_name="Last name 1", type=ContactType.PERSON
    )
    tenant_contact_factory(
        type=TenantContactType.TENANT,
        tenant=tenant1,
        contact=contact1,
        start_date=date(year=2000, month=1, day=1),
    )

    tenant2 = tenant_factory(lease=lease, share_numerator=1, share_denominator=3)
    tenant_rent_share_factory(
        tenant=tenant2, intended_use_id=1, share_numerator=1, share_denominator=3
    )
    contact2 = contact_factory(
        first_name="First name 2", last_name="Last name 2", type=ContactType.PERSON
    )
    tenant_contact_factory(
        type=TenantContactType.TENANT,
        tenant=tenant2,
        contact=contact2,
        start_date=date(year=2000, month=1, day=1),
    )

    tenant3 = tenant_factory(lease=lease, share_numerator=1, share_denominator=3)
    tenant_rent_share_factory(
        tenant=tenant3, intended_use_id=1, share_numerator=1, share_denominator=3
    )
    contact3 = contact_factory(
        first_name="First name 3", last_name="Last name 3", type=ContactType.PERSON
    )
    tenant_contact_factory(
        type=TenantContactType.TENANT,
        tenant=tenant3,
        contact=contact3,
        start_date=date(year=2000, month=1, day=1),
    )

    rent: Rent = rent_factory(
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

    billing_period = (
        date(year=2017, month=1, day=1),
        date(year=2017, month=12, day=31),
    )

    calculation_result = CalculationResult(*billing_period)
    calculation_result.add_amount(
        CalculationAmount(
            item=contract_rent,
            amount=Decimal(1000),
            date_range_start=billing_period[0],
            date_range_end=billing_period[1],
        )
    )

    period_rents: PayableRentsInPeriods = {
        billing_period: {
            "due_date": date(year=2017, month=6, day=1),
            "calculation_result": calculation_result,
            "last_billing_period": False,
            "override_receivable_type": rent.get_override_receivable_type(),
        }
    }

    invoice_data = lease.calculate_invoices(period_rents)

    assert len(invoice_data) == 1
    assert len(invoice_data[0]) == 3
    assert len(invoice_data[0][0]["rows"]) == 1
    assert len(invoice_data[0][1]["rows"]) == 1
    assert len(invoice_data[0][2]["rows"]) == 1

    amounts = [
        invoice_data[0][0]["billed_amount"],
        invoice_data[0][1]["billed_amount"],
        invoice_data[0][2]["billed_amount"],
    ]

    assert_count_equal(
        amounts, [Decimal("333.33"), Decimal("333.33"), Decimal("333.34")]
    )

    tenants = {
        invoice_data[0][0]["rows"][0]["tenant"],
        invoice_data[0][1]["rows"][0]["tenant"],
        invoice_data[0][2]["rows"][0]["tenant"],
    }

    assert tenants == {tenant1, tenant2, tenant3}


@pytest.mark.django_db
def test_calculate_invoices_seasonal(
    lease_test_data, tenant_rent_share_factory, rent_factory, contract_rent_factory
):
    lease: Lease = lease_test_data["lease"]
    tenant1 = lease_test_data["tenants"][0]
    tenant_rent_share_factory(
        tenant=tenant1, intended_use_id=1, share_numerator=1, share_denominator=1
    )

    rent1 = rent_factory(
        lease=lease,
        type=RentType.FIXED,
        due_dates_type=DueDatesType.FIXED,
        due_dates_per_year=12,
        start_date=None,
        end_date=date(year=2019, month=12, day=31),
    )
    contract_rent_factory(
        rent=rent1,
        intended_use_id=1,
        amount=80,
        period=PeriodType.PER_MONTH,
        base_amount=80,
        base_amount_period=PeriodType.PER_MONTH,
        start_date=date(year=2018, month=10, day=1),
        end_date=date(year=2019, month=6, day=30),
    )
    contract_rent_factory(
        rent=rent1,
        intended_use_id=1,
        amount=80,
        period=PeriodType.PER_MONTH,
        base_amount=80,
        base_amount_period=PeriodType.PER_MONTH,
        start_date=date(year=2019, month=10, day=1),
        end_date=date(year=2020, month=6, day=30),
    )

    rent2 = rent_factory(
        lease=lease,
        type=RentType.FIXED,
        due_dates_type=DueDatesType.CUSTOM,
        start_date=date(year=2020, month=1, day=1),
        end_date=None,
        seasonal_start_day=1,
        seasonal_start_month=1,
        seasonal_end_day=30,
        seasonal_end_month=6,
    )
    rent2.due_dates.add(RentDueDate.objects.create(rent=rent2, month=2, day=1))
    rent2.due_dates.add(RentDueDate.objects.create(rent=rent2, month=3, day=1))
    rent2.due_dates.add(RentDueDate.objects.create(rent=rent2, month=4, day=1))
    rent2.due_dates.add(RentDueDate.objects.create(rent=rent2, month=5, day=1))
    rent2.due_dates.add(RentDueDate.objects.create(rent=rent2, month=1, day=1))
    rent2.due_dates.add(RentDueDate.objects.create(rent=rent2, month=6, day=1))

    contract_rent_factory(
        rent=rent2,
        intended_use_id=1,
        amount=80,
        period=PeriodType.PER_MONTH,
        base_amount=80,
        base_amount_period=PeriodType.PER_MONTH,
    )

    rent3 = rent_factory(
        lease=lease,
        type=RentType.FIXED,
        due_dates_type=DueDatesType.CUSTOM,
        start_date=date(year=2020, month=1, day=1),
        end_date=None,
        seasonal_start_day=1,
        seasonal_start_month=7,
        seasonal_end_day=30,
        seasonal_end_month=9,
    )
    rent3.due_dates.add(RentDueDate.objects.create(rent=rent3, month=7, day=1))

    contract_rent_factory(
        rent=rent3,
        intended_use_id=1,
        amount=120,
        period=PeriodType.PER_MONTH,
        base_amount=120,
        base_amount_period=PeriodType.PER_MONTH,
    )

    rent4 = rent_factory(
        lease=lease,
        type=RentType.FIXED,
        due_dates_type=DueDatesType.CUSTOM,
        start_date=date(year=2020, month=1, day=1),
        end_date=None,
        seasonal_start_day=1,
        seasonal_start_month=10,
        seasonal_end_day=31,
        seasonal_end_month=12,
    )
    rent4.due_dates.add(RentDueDate.objects.create(rent=rent4, month=10, day=1))
    rent4.due_dates.add(RentDueDate.objects.create(rent=rent4, month=11, day=1))
    rent4.due_dates.add(RentDueDate.objects.create(rent=rent4, month=12, day=1))

    contract_rent_factory(
        rent=rent4,
        intended_use_id=1,
        amount=80,
        period=PeriodType.PER_MONTH,
        base_amount=80,
        base_amount_period=PeriodType.PER_MONTH,
    )

    first_day_of_year = date(year=2020, month=1, day=1)
    first_day_of_every_month = [
        dt.date() for dt in rrule(freq=MONTHLY, count=12, dtstart=first_day_of_year)
    ]

    total_invoice_amount = Decimal(0)
    total_invoice_row_amount = Decimal(0)

    for first_day in first_day_of_every_month:
        last_day = first_day + relativedelta(day=31)

        rents = lease.determine_payable_rents_and_periods(
            first_day, last_day, dry_run=True
        )

        for period_invoice_data in lease.calculate_invoices(rents):
            for invoice_data in period_invoice_data:
                total_invoice_amount += invoice_data["billed_amount"]
                total_invoice_row_amount += sum(
                    [row["amount"] for row in invoice_data["rows"]]
                )

    assert total_invoice_amount == total_invoice_row_amount
    assert total_invoice_amount == Decimal(1080)


@pytest.mark.django_db
def test_calculate_invoices_uses_correct_receivable_type(
    django_db_setup,
    service_unit_factory,
    receivable_type_factory,
    lease_factory,
    tenant_factory,
    contact_factory,
    tenant_contact_factory,
    tenant_rent_share_factory,
    rent_factory,
    contract_rent_factory,
):
    service_units = [
        service_unit_factory(name="First service unit"),
        service_unit_factory(name="Second service unit"),
    ]

    for service_unit in service_units:
        receivable_type = receivable_type_factory(
            name="Maanvuokraus", service_unit=service_unit
        )
        service_unit.default_receivable_type_rent = receivable_type

        lease: Lease = lease_factory(
            type_id=1,
            municipality_id=1,
            district_id=1,
            notice_period_id=1,
            start_date=date(year=2000, month=1, day=1),
            service_unit=service_unit,
        )

        tenant1 = tenant_factory(lease=lease, share_numerator=1, share_denominator=1)
        tenant_rent_share_factory(
            tenant=tenant1, intended_use_id=1, share_numerator=1, share_denominator=1
        )
        contact1 = contact_factory(
            first_name="First name 1",
            last_name="Last name 1",
            type=ContactType.PERSON,
            service_unit=service_unit,
        )
        tenant_contact_factory(
            type=TenantContactType.TENANT,
            tenant=tenant1,
            contact=contact1,
            start_date=date(year=2000, month=1, day=1),
        )

        rent: Rent = rent_factory(
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

        billing_period = (
            date(year=2017, month=1, day=1),
            date(year=2017, month=12, day=31),
        )

        calculation_result = CalculationResult(*billing_period)
        calculation_result.add_amount(
            CalculationAmount(
                item=contract_rent,
                amount=Decimal(1000),
                date_range_start=billing_period[0],
                date_range_end=billing_period[1],
            )
        )

        period_rents: PayableRentsInPeriods = {
            billing_period: {
                "due_date": date(year=2017, month=6, day=1),
                "calculation_result": calculation_result,
                "last_billing_period": False,
                "override_receivable_type": rent.get_override_receivable_type(),
            }
        }

        invoice_data = lease.calculate_invoices(period_rents)

        assert len(invoice_data) == 1
        assert len(invoice_data[0]) == 1
        assert invoice_data[0][0]["rows"][0]["receivable_type"] == receivable_type
