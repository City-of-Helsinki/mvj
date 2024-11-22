from datetime import date
from decimal import Decimal

import pytest

from leasing.calculation.result import CalculationAmount, CalculationResult
from leasing.enums import (
    ContactType,
    DueDatesType,
    PeriodType,
    RentCycle,
    RentType,
    TenantContactType,
)
from leasing.models import Lease, Rent, ServiceUnit
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
    lease = lease_factory(
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

    period_rents = {
        billing_period: {
            "due_date": date(year=2017, month=6, day=1),
            "calculation_result": calculation_result,
            "last_billing_period": False,
            "override_receivable_type": None,
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
    lease = lease_factory(
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

    period_rents = {
        billing_period: {
            "due_date": date(year=2017, month=6, day=1),
            "calculation_result": calculation_result,
            "last_billing_period": False,
            "override_receivable_type": None,
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
    lease = lease_factory(
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

    period_rents = {
        billing_period: {
            "due_date": date(year=2017, month=6, day=1),
            "calculation_result": calculation_result,
            "last_billing_period": False,
            "override_receivable_type": None,
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
    """
    By default, invoice generation uses the service unit's default
    receivable type for rents, if no other receivable types are specified.
    """
    service_units = [
        service_unit_factory(name="First service unit"),
        service_unit_factory(name="Second service unit"),
    ]

    for service_unit in service_units:
        receivable_type = receivable_type_factory(
            name="Maanvuokraus", service_unit=service_unit
        )
        service_unit.default_receivable_type_rent = receivable_type

        lease = lease_factory(
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

        period_rents = {
            billing_period: {
                "due_date": date(year=2017, month=6, day=1),
                "calculation_result": calculation_result,
                "last_billing_period": False,
                "override_receivable_type": None,
            }
        }

        invoice_data = lease.calculate_invoices(period_rents)

        assert len(invoice_data) == 1
        assert len(invoice_data[0]) == 1
        assert invoice_data[0][0]["rows"][0]["receivable_type"] == receivable_type


@pytest.mark.django_db
def test_calculate_invoices_uses_override_receivable_type(
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
    """
    If an override_receivable_type is defined in a rent, that receivable type is
    used in the invoice generation over the service unit's
    default_receivable_type_rent.
    """
    # Mandatory set up
    service_unit: ServiceUnit = service_unit_factory(name="ServiceUnitName")
    service_unit.default_receivable_type_rent = receivable_type_factory(
        name="Maanvuokraus", service_unit=service_unit
    )
    lease: Lease = lease_factory(
        type_id=1,
        municipality_id=1,
        district_id=1,
        notice_period_id=1,
        start_date=date(year=2000, month=1, day=1),
        service_unit=service_unit,
    )
    tenant = tenant_factory(lease=lease, share_numerator=1, share_denominator=1)
    tenant_rent_share_factory(
        tenant=tenant, intended_use_id=1, share_numerator=1, share_denominator=1
    )
    contact = contact_factory(
        first_name="ContactFirstName",
        last_name="ContactLastName",
        type=ContactType.PERSON,
        service_unit=service_unit,
    )
    tenant_contact_factory(
        type=TenantContactType.TENANT,
        tenant=tenant,
        contact=contact,
        start_date=date(year=2000, month=1, day=1),
    )
    # Set the receivable type override that should be in invoice
    override_receivable_type = receivable_type_factory(
        name="OverrideReceivableType", service_unit=service_unit
    )
    rent: Rent = rent_factory(
        lease=lease,
        type=RentType.FIXED,
        cycle=RentCycle.JANUARY_TO_DECEMBER,
        due_dates_type=DueDatesType.FIXED,
        due_dates_per_year=1,
        override_receivable_type=override_receivable_type,
    )

    # Billing item calculations
    billing_period = (
        date(year=2020, month=1, day=1),
        date(year=2020, month=12, day=31),
    )
    calculation_result = CalculationResult(*billing_period)
    contract_rent1 = contract_rent_factory(
        rent=rent,
        intended_use_id=1,
        amount=1000,
        period=PeriodType.PER_YEAR,
        base_amount=1000,
        base_amount_period=PeriodType.PER_YEAR,
    )
    calculation_result.add_amount(
        CalculationAmount(
            item=contract_rent1,
            amount=Decimal(1000),
            date_range_start=billing_period[0],
            date_range_end=billing_period[1],
        )
    )
    period_rents: PayableRentsInPeriods = {
        billing_period: {
            "due_date": date(year=2020, month=6, day=1),
            "calculation_result": calculation_result,
            "last_billing_period": False,
            "override_receivable_type": rent.override_receivable_type,
        }
    }

    # Calculate the results
    invoice_data = lease.calculate_invoices(period_rents)

    # Test that override receivable type is used by the invoice
    invoice_datum = invoice_data[0][0]
    assert invoice_datum["rows"][0]["receivable_type"] == override_receivable_type
