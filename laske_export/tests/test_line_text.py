import datetime
from decimal import Decimal

import pytest

from laske_export.document.invoice_sales_order_adapter import (
    AkvInvoiceSalesOrderAdapter,
    invoice_sales_order_adapter_factory,
)
from laske_export.exporter import create_sales_order_with_laske_values
from leasing.enums import ContactType, ServiceUnitId, TenantContactType
from leasing.models import ServiceUnit


@pytest.mark.django_db
def test_akv_line_text(
    django_db_setup,
    contact_factory,
    decision_factory,
    district_factory,
    intended_use_factory,
    invoice_factory,
    invoice_row_factory,
    lease_factory,
    lease_area_factory,
    lease_area_address_factory,
    receivable_type_factory,
    rent_intended_use_factory,
    tenant_factory,
    tenant_contact_factory,
):
    """Test the AKV line text creation."""
    service_unit = ServiceUnit.objects.get(pk=ServiceUnitId.AKV)
    lessor = contact_factory(service_unit=service_unit, sap_sales_office="1234")
    district = district_factory(identifier="99", name="DistrictName")
    intended_use = intended_use_factory(
        name="IntendedUseName", service_unit=service_unit
    )
    lease = lease_factory(
        service_unit=service_unit,
        lessor=lessor,
        district=district,
        intended_use=intended_use,
    )
    decision = decision_factory(
        lease=lease,
        reference_number="HEL 2024-123456",
        decision_date=datetime.date(year=2024, month=1, day=1),
        section="111",
    )

    # Set up lease areas.
    # Lease can have multiple LeaseAreas, which can have multiple LeaseAreaAddresses
    lease_area1 = lease_area_factory(
        lease=lease,
        area=100,
        archived_decision=decision,
    )
    lease_area_address_factory(
        lease_area=lease_area1,
        address="LeaseArea1Address 1",
        postal_code="00100",
        city="LeaseAreaCity",
        is_primary=False,  # Non-primary address should be ignored if primary address exists
    )
    lease_area1_address2 = lease_area_address_factory(
        lease_area=lease_area1,
        address="LeaseArea1Address 2",
        postal_code="00100",
        city="LeaseAreaCity",
        is_primary=True,  # This address should be selected: first area, primary address
    )
    # Rest of the areas and their addresses should be left out of the line text
    lease_area_factory(lease=lease, area=200)
    lease_area_address_factory(
        lease_area=lease_area1,
        address="LeaseArea2Address 1",
        postal_code="00100",
        city="LeaseAreaCity",
        is_primary=False,
    )
    lease_area_address_factory(
        lease_area=lease_area1,
        address="LeaseArea2Address 2",
        postal_code="00100",
        city="LeaseAreaCity",
        is_primary=True,
    )

    # Set up invoice
    tenant = tenant_factory(
        lease=lease,
        share_numerator=1,
        share_denominator=1,
        reference="Tenant1Reference",
    )
    contact = contact_factory(
        type=ContactType.PERSON,
        first_name="Contact1FirstName",
        last_name="Contact1LastName",
    )
    tenant_contact_factory(
        type=TenantContactType.TENANT,
        tenant=tenant,
        contact=contact,
        start_date=datetime.date(year=2024, month=1, day=1),
    )
    billing_period_start_date = datetime.date(year=2024, month=1, day=1)
    billing_period_end_date = datetime.date(year=2024, month=12, day=31)

    invoice = invoice_factory(
        lease=lease,
        total_amount=Decimal("123.45"),
        billed_amount=Decimal("123.45"),
        outstanding_amount=Decimal("123.45"),
        recipient=contact_factory(
            first_name="RecipientFirstName",
            last_name="RecipientLastName",
            type=ContactType.PERSON,
        ),
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
    )
    receivable_type = receivable_type_factory(service_unit=service_unit)
    intended_use = rent_intended_use_factory(name="Muu")
    invoice_row_factory(
        invoice=invoice,
        tenant=tenant,
        receivable_type=receivable_type,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
        amount=Decimal("123.45"),
        intended_use=intended_use,
    )
    sales_order = create_sales_order_with_laske_values(invoice.service_unit)

    adapter = invoice_sales_order_adapter_factory(
        invoice=invoice,
        sales_order=sales_order,
        receivable_type_rent=receivable_type,
        receivable_type_collateral=receivable_type_factory(service_unit=service_unit),
    )
    adapter.set_values()

    # Verify that invoice line text has been set correctly
    line_item = adapter.sales_order.line_items[0]
    line_texts = []
    for i in range(1, 7):
        line_texts.append(getattr(line_item, f"line_text_l{i}", ""))

    date_format = AkvInvoiceSalesOrderAdapter.AKV_DATE_FORMAT
    combined_line_text = "".join(line_texts)

    assert intended_use.name in combined_line_text
    assert str(lease_area1.area) in combined_line_text
    assert district.name in combined_line_text
    assert district.identifier in combined_line_text
    assert lease_area1_address2.address in combined_line_text
    assert lease_area1_address2.postal_code in combined_line_text
    assert decision.reference_number in combined_line_text
    assert decision.decision_date.strftime(date_format) in combined_line_text
    assert decision.section in combined_line_text
    assert billing_period_start_date.strftime(date_format) in combined_line_text
    assert billing_period_end_date.strftime(date_format) in combined_line_text
