import datetime
from decimal import Decimal
from typing import Any, Callable

import pytest

from laske_export.document.invoice_sales_order_adapter import (
    InvoiceSalesOrderAdapter,
    _sort_invoice_rows_for_lineitems,
    invoice_sales_order_adapter_factory,
)
from laske_export.document.sales_order import LineItem
from laske_export.exporter import create_sales_order_with_laske_values
from leasing.enums import ServiceUnitId, TenantContactType
from leasing.models.contact import Contact
from leasing.models.invoice import Invoice, InvoiceRow
from leasing.models.lease import Lease, LeaseType
from leasing.models.receivable_type import ReceivableType
from leasing.models.service_unit import ServiceUnit
from leasing.models.tenant import Tenant, TenantContact


@pytest.mark.parametrize(
    # Pass the ID to the test setup fixture
    "exporter_lacking_test_setup",
    [ServiceUnitId.KAMA],
    indirect=True,
)
@pytest.mark.django_db
def test_set_line_item_common_values_sap_receivable_type(
    exporter_lacking_test_setup: dict[str, Any],
):
    """Verifies that only one of 'wbs_element' and 'order_item_number' is set.
    If 'sap_project_number' is set, it should be set to 'wbs_element'.
    When 'sap_project_number' is set, 'sap_order_item_number' should be ignored.
    Otherwise, 'sap_order_item_number' should be set to 'order_item_number'.
    """
    adapter: InvoiceSalesOrderAdapter = exporter_lacking_test_setup["adapter"]
    invoice_row: InvoiceRow = exporter_lacking_test_setup["invoicerow1"]
    receivable_type: ReceivableType = invoice_row.receivable_type

    receivable_type.sap_project_number = "123"
    receivable_type.sap_order_item_number = None
    receivable_type.save()
    receivable_type.refresh_from_db()
    line_item = LineItem()
    adapter.set_line_item_common_values(line_item, invoice_row)
    assert line_item.wbs_element == "123"
    assert line_item.order_item_number is None

    receivable_type.sap_project_number = "123"
    receivable_type.sap_order_item_number = "456"
    receivable_type.save()
    receivable_type.refresh_from_db()
    line_item = LineItem()
    adapter.set_line_item_common_values(line_item, invoice_row)
    assert line_item.wbs_element == "123"
    assert line_item.order_item_number is None

    receivable_type.sap_project_number = None
    receivable_type.sap_order_item_number = "456"
    receivable_type.save()
    receivable_type.refresh_from_db()
    line_item = LineItem()
    adapter.set_line_item_common_values(line_item, invoice_row)
    assert line_item.wbs_element is None
    assert line_item.order_item_number == "456"


@pytest.mark.parametrize(
    # Pass the ID to the test setup fixture
    "exporter_lacking_test_setup",
    [ServiceUnitId.KAMA],
    indirect=True,
)
@pytest.mark.django_db
def test_set_line_item_common_values_sap_lease_type(
    exporter_lacking_test_setup: dict[str, Any],
):
    """Tests logic for handling values from LeaseType."""
    adapter: InvoiceSalesOrderAdapter = exporter_lacking_test_setup["adapter"]
    invoice_row: InvoiceRow = exporter_lacking_test_setup["invoicerow1"]
    receivable_type: ReceivableType = invoice_row.receivable_type
    lease_type: LeaseType = invoice_row.invoice.lease.type
    invoice_service_unit: ServiceUnit = invoice_row.invoice.service_unit
    invoice_service_unit.default_receivable_type_rent = receivable_type
    invoice_service_unit.save()

    # Lease.internal_order is not set, ReceivableType does not have SAP values set.
    # Use LeaseType.sap_project_number
    lease_type.sap_project_number = "project_nr"
    lease_type.sap_order_item_number = None
    lease_type.save()
    line_item = LineItem()
    adapter.set_line_item_common_values(line_item, invoice_row)
    assert line_item.wbs_element == "project_nr"
    assert line_item.order_item_number is None

    # Lease.internal_order is not set, ReceivableType does not have SAP values set.
    # Use LeaseType.sap_project_number when also sap_order_item_number is set.
    lease_type.sap_project_number = "project_nr"
    lease_type.sap_order_item_number = "ord_nr"
    lease_type.save()
    line_item = LineItem()
    adapter.set_line_item_common_values(line_item, invoice_row)
    assert line_item.wbs_element == "project_nr"
    assert line_item.order_item_number is None

    # Lease.internal_order is not set, ReceivableType does not have SAP values set.
    # Use LeaseType.sap_order_item_number
    lease_type.sap_project_number = None
    lease_type.sap_order_item_number = "ord_nr"
    lease_type.save()
    line_item = LineItem()
    adapter.set_line_item_common_values(line_item, invoice_row)
    assert line_item.wbs_element is None
    assert line_item.order_item_number == "ord_nr"


@pytest.mark.parametrize(
    # Pass the ID to the test setup fixture
    "exporter_lacking_test_setup",
    [ServiceUnitId.KAMA],
    indirect=True,
)
@pytest.mark.django_db
def test_set_line_item_common_values_sap_lease_internal_order(
    exporter_lacking_test_setup: dict[str, Any],
):
    """Tests logic for handling case when `Lease.internal_order` is set,
    which is expected to overwrite values when the conditions are right.
    """
    adapter: InvoiceSalesOrderAdapter = exporter_lacking_test_setup["adapter"]
    invoice_row: InvoiceRow = exporter_lacking_test_setup["invoicerow1"]
    receivable_type: ReceivableType = invoice_row.receivable_type
    lease: Lease = invoice_row.invoice.lease
    lease_type: LeaseType = invoice_row.invoice.lease.type
    invoice_service_unit: ServiceUnit = invoice_row.invoice.service_unit
    invoice_service_unit.default_receivable_type_rent = receivable_type
    invoice_service_unit.save()

    # Lease.internal_order is set, ReceivableType does not have SAP values set.
    # Expect line_item.order_item_number to be set to Lease.internal_order
    lease_type.sap_project_number = None
    lease_type.sap_order_item_number = "o_nr_notused"
    lease_type.save()
    lease.internal_order = "internal_ord"
    lease.save()
    line_item = LineItem()
    adapter.set_line_item_common_values(line_item, invoice_row)
    assert line_item.wbs_element is None
    assert line_item.order_item_number == "internal_ord"

    # Lease.internal_order is set, ReceivableType does not have SAP values set.
    # LeaseType.sap_project_number is set but overwritten, and wbs_element is not set.
    # Expect line_item.order_item_number to be set to Lease.internal_order
    lease_type.sap_project_number = "pr_nr_not_used"
    lease_type.sap_order_item_number = None
    lease_type.save()
    lease.internal_order = "internal_ord"
    lease.save()
    line_item = LineItem()
    adapter.set_line_item_common_values(line_item, invoice_row)
    assert line_item.wbs_element is None
    assert line_item.order_item_number == "internal_ord"


@pytest.mark.parametrize(
    "exporter_full_test_setup",
    [ServiceUnitId.MAKE, ServiceUnitId.KAMA],
    indirect=True,
)
@pytest.mark.django_db
def test_get_sorted_invoice_rows(exporter_full_test_setup: dict[str, Any]):
    """Test that invoice rows are properly sorted by amount."""
    invoice: Invoice = exporter_full_test_setup["invoice1"]
    InvoiceRow.objects.all().filter(invoice_id=invoice.id).delete()
    assert InvoiceRow.objects.count() == 0

    receivable_type = exporter_full_test_setup["invoicerow1_receivable_type"]

    charge_smaller = InvoiceRow.objects.create(
        invoice=invoice,
        amount=Decimal("100.00"),
        receivable_type=receivable_type,
    )
    rounding_negative = InvoiceRow.objects.create(
        invoice=invoice,
        amount=Decimal("-0.05"),
        receivable_type=receivable_type,
    )
    credit_smaller = InvoiceRow.objects.create(
        invoice=invoice,
        amount=Decimal("-25.00"),
        receivable_type=receivable_type,
    )
    rounding_positive = InvoiceRow.objects.create(
        invoice=invoice,
        amount=Decimal("0.01"),
        receivable_type=receivable_type,
    )
    charge_larger = InvoiceRow.objects.create(
        invoice=invoice,
        amount=Decimal("200.00"),
        receivable_type=receivable_type,
    )
    credit_larger = InvoiceRow.objects.create(
        invoice=invoice,
        amount=Decimal("-50.00"),
        receivable_type=receivable_type,
    )

    # Get sorted rows
    sorted_rows = _sort_invoice_rows_for_lineitems(invoice.rows.all())

    # Expected order:
    # 1. Charges (positive amounts) in descending order: 200, 100
    # 2. Credits (negative amounts) in descending absolute order: -50, -25
    # 3. Roundings (small amounts) in descending order: 0.01, -0.05
    expected_order = [
        charge_larger,
        charge_smaller,
        credit_larger,
        credit_smaller,
        rounding_positive,
        rounding_negative,
    ]

    assert len(sorted_rows) == 6
    assert sorted_rows == expected_order


@pytest.mark.parametrize(
    # Pass the ID to the test setup fixture
    "invoice_sales_order_adapter_billing_contact_test_setup",
    [ServiceUnitId.MAKE, ServiceUnitId.KAMA],
    indirect=True,
)
@pytest.mark.django_db
def test_get_contact_to_bill_returns_billing_contacts_new_contact(
    invoice_sales_order_adapter_billing_contact_test_setup: dict[str, Any],
    tenant_factory: Callable[..., Tenant],
    tenant_contact_factory: Callable[..., TenantContact],
    contact_factory: Callable[..., Contact],
    invoice_factory: Callable[..., Invoice],
    invoice_row_factory: Callable[..., InvoiceRow],
):
    """
    Case: Billing contact's contact (laskunsaajan asiakas) is changed to another
          contact in the UI.

    Note: This is not the preferred procedure for changing the billing contact,
    because there is no trace of dates for the change, but it is technically
    possible.
    The preferred way is to end the existing billing contact and create a new
    one, which is tested in another test case.

    Given:
    - billing contact (type=billing),
    - invoice for this billing contact,
    - invoice rows for this tenant,
    - billing period when the contacts are active,

    When:
    - the billing contact's contact is changed to a new contact,

    Then:
    - get_contact_to_bill() should return the billing contact's new contact,
        because they are the designated billing contact for the lease during the
        invoice's billing period.
    """
    # Given...
    lease: Lease = invoice_sales_order_adapter_billing_contact_test_setup["lease"]
    service_unit: ServiceUnit = invoice_sales_order_adapter_billing_contact_test_setup[
        "service_unit"
    ]

    tenant = tenant_factory(
        lease=lease,
        share_numerator=1,
        share_denominator=1,
        reference=None,
    )

    # Tenantcontacts that are active for whole year of 2026.
    tenant_contacts_contact = contact_factory(first_name="Tenant", last_name="Contact")
    tenant_contact_factory(
        type=TenantContactType.TENANT,
        tenant=tenant,
        contact=tenant_contacts_contact,
        start_date=datetime.date(2026, 1, 1),
    )

    original_contact = contact_factory(
        first_name="Billing", last_name="Contact Original"
    )

    billing_contact = tenant_contact_factory(
        type=TenantContactType.BILLING,
        tenant=tenant,
        contact=original_contact,
        start_date=datetime.date(2026, 1, 1),
    )

    # Invoice for December 2026.
    billing_period_start_date = datetime.date(year=2026, month=12, day=1)
    billing_period_end_date = datetime.date(year=2026, month=12, day=31)

    invoice = invoice_factory(
        lease=lease,
        total_amount=Decimal("111.11"),
        billed_amount=Decimal("111.11"),
        outstanding_amount=Decimal("111.11"),
        recipient=original_contact,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
    )
    invoicerow_receivable_type: ReceivableType = (
        invoice_sales_order_adapter_billing_contact_test_setup[
            "invoicerow_receivable_type"
        ]
    )
    invoice_row_factory(
        invoice=invoice,
        tenant=tenant,
        receivable_type=invoicerow_receivable_type,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
        amount=Decimal("111.11"),
    )

    # When...
    new_contact = contact_factory(
        first_name="Billing",
        last_name="Contact New",
    )
    billing_contact.contact = new_contact
    billing_contact.save()

    sales_order = create_sales_order_with_laske_values(service_unit)
    adapter = invoice_sales_order_adapter_factory(
        invoice=invoice,
        sales_order=sales_order,
        service_unit=service_unit,
    )

    # Then...
    assert adapter.get_contact_to_bill() == new_contact


@pytest.mark.django_db
@pytest.mark.parametrize(
    # Pass the ID to the test setup fixture
    "invoice_sales_order_adapter_billing_contact_test_setup",
    [ServiceUnitId.MAKE, ServiceUnitId.KAMA],
    indirect=True,
)
def test_get_contact_to_bill_when_billing_contact_covers_billing_period_but_ends_afterwards(
    invoice_sales_order_adapter_billing_contact_test_setup: dict[str, Any],
    tenant_factory: Callable[..., Tenant],
    tenant_contact_factory: Callable[..., TenantContact],
    contact_factory: Callable[..., Contact],
    invoice_factory: Callable[..., Invoice],
    invoice_row_factory: Callable[..., InvoiceRow],
):
    """
    Case: Billing contact covers the invoice's billing period, but it ends afterwards.

    Given:
    - tenant contact (type=tenant),
    - billing contact (type=billing),
    - invoice for this billing contact,
    - invoice rows for this tenant,
    - billing period when the contacts are active,

    When:
    - billing contact ends after the billing period,

    Then:
    - get_contact_to_bill() should return the billing contact's contact, because
        they are still responsible for the invoice's billing period.
    """
    # Given...
    lease: Lease = invoice_sales_order_adapter_billing_contact_test_setup["lease"]
    service_unit: ServiceUnit = invoice_sales_order_adapter_billing_contact_test_setup[
        "service_unit"
    ]

    tenant = tenant_factory(
        lease=lease,
        share_numerator=1,
        share_denominator=1,
        reference=None,
    )

    tenant_contacts_contact = contact_factory(first_name="Tenant", last_name="Contact")
    tenant_contact_factory(
        type=TenantContactType.TENANT,
        tenant=tenant,
        contact=tenant_contacts_contact,
        start_date=datetime.date(2026, 1, 1),
    )

    billing_contact_person = contact_factory(first_name="Billing", last_name="Contact")
    billing_contact = tenant_contact_factory(
        type=TenantContactType.BILLING,
        tenant=tenant,
        contact=billing_contact_person,
        start_date=datetime.date(2026, 1, 1),
    )

    # Invoice for December 2026.
    billing_period_start_date = datetime.date(year=2026, month=12, day=1)
    billing_period_end_date = datetime.date(year=2026, month=12, day=31)

    invoice = invoice_factory(
        lease=lease,
        total_amount=Decimal("111.11"),
        billed_amount=Decimal("111.11"),
        outstanding_amount=Decimal("111.11"),
        recipient=billing_contact_person,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
    )
    invoicerow_receivable_type: ReceivableType = (
        invoice_sales_order_adapter_billing_contact_test_setup[
            "invoicerow_receivable_type"
        ]
    )
    invoice_row_factory(
        invoice=invoice,
        tenant=tenant,
        receivable_type=invoicerow_receivable_type,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
        amount=Decimal("111.11"),
    )

    # When...
    billing_contact.end_date = datetime.date(2027, 1, 31)
    billing_contact.save()

    sales_order = create_sales_order_with_laske_values(service_unit)
    adapter = invoice_sales_order_adapter_factory(
        invoice=invoice,
        sales_order=sales_order,
        service_unit=service_unit,
    )

    # Then...
    assert adapter.get_contact_to_bill() == billing_contact_person


@pytest.mark.django_db
@pytest.mark.parametrize(
    # Pass the ID to the test setup fixture
    "invoice_sales_order_adapter_billing_contact_test_setup",
    [ServiceUnitId.MAKE, ServiceUnitId.KAMA],
    indirect=True,
)
def test_get_contact_to_bill_when_no_active_tenants(
    invoice_sales_order_adapter_billing_contact_test_setup: dict[str, Any],
    tenant_factory: Callable[..., Tenant],
    tenant_contact_factory: Callable[..., TenantContact],
    contact_factory: Callable[..., Contact],
    invoice_factory: Callable[..., Invoice],
    invoice_row_factory: Callable[..., InvoiceRow],
):
    """
    Case: Invoice was created for a tenant, but afterwards that tenant was ended.
          A new tenant was added, who covers the invoice's period.

    The system should send the invoice to original receiver, who will probably
    raise the issue with Helsinki if there is a problem that is not handled by
    Helsinki invoicers beforehand.

    Such cases always require human review and intervention. The new tenant's
    conditions are likely different from the previous tenant's conditions, which
    means the existing invoice's contents might not be valid anymore.

    Given:
    - tenant,
    - tenant contact (type=tenant),
    - billing contact (type=billing),
    - invoice for this billing contact,
    - invoice rows for this tenant,
    - billing period when the contacts are active,

    When:
    - the tenant ends (== tenantcontact of type=tenant ends),
    - billing contact ends,
    - new tenant is added, that covers the billing period,

    Then:
    - get_contact_to_bill() should return the invoice's original recipient,
      because any changes cannot be automatically handled at this point.
    """
    # Given...
    lease: Lease = invoice_sales_order_adapter_billing_contact_test_setup["lease"]
    service_unit: ServiceUnit = invoice_sales_order_adapter_billing_contact_test_setup[
        "service_unit"
    ]

    original_tenant = tenant_factory(
        lease=lease,
        share_numerator=1,
        share_denominator=1,
        reference=None,
    )

    # Tenantcontacts that are active for whole year of 2026.
    tenant_contacts_contact = contact_factory(
        first_name="Original Tenant", last_name="Contact"
    )
    original_tenant_contact = tenant_contact_factory(
        type=TenantContactType.TENANT,
        tenant=original_tenant,
        contact=tenant_contacts_contact,
        start_date=datetime.date(2026, 1, 1),
    )

    original_contact = contact_factory(
        first_name="Original Billing", last_name="Contact"
    )
    original_billing_contact = tenant_contact_factory(
        type=TenantContactType.BILLING,
        tenant=original_tenant,
        contact=original_contact,
        start_date=datetime.date(2026, 1, 1),
    )

    # Invoice for December 2026.
    billing_period_start_date = datetime.date(year=2026, month=12, day=1)
    billing_period_end_date = datetime.date(year=2026, month=12, day=31)

    invoice = invoice_factory(
        lease=lease,
        total_amount=Decimal("111.11"),
        billed_amount=Decimal("111.11"),
        outstanding_amount=Decimal("111.11"),
        recipient=original_contact,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
    )
    invoicerow_receivable_type: ReceivableType = (
        invoice_sales_order_adapter_billing_contact_test_setup[
            "invoicerow_receivable_type"
        ]
    )
    invoice_row_factory(
        invoice=invoice,
        tenant=original_tenant,
        receivable_type=invoicerow_receivable_type,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
        amount=Decimal("111.11"),
    )

    # When...
    # Old tenant is ended before invoice's billing period
    original_tenant_contact.end_date = datetime.date(2026, 11, 30)
    original_tenant_contact.save()
    original_billing_contact.end_date = datetime.date(2026, 11, 30)
    original_billing_contact.save()

    # New tenant starts during invoice's billing period.
    new_tenant = tenant_factory(
        lease=lease,
        share_numerator=1,
        share_denominator=1,
        reference=None,
    )
    new_tenant_contacts_contact = contact_factory(
        first_name="New Tenant", last_name="Contact"
    )
    tenant_contact_factory(
        type=TenantContactType.TENANT,
        tenant=new_tenant,
        contact=new_tenant_contacts_contact,
        start_date=datetime.date(2026, 12, 1),
    )
    new_billing_contacts_contact = contact_factory(
        first_name="New Billing",
        last_name="Contact",
    )
    tenant_contact_factory(
        type=TenantContactType.BILLING,
        tenant=new_tenant,
        contact=new_billing_contacts_contact,
        start_date=datetime.date(2026, 12, 1),
    )
    sales_order = create_sales_order_with_laske_values(service_unit)
    adapter = invoice_sales_order_adapter_factory(
        invoice=invoice,
        sales_order=sales_order,
        service_unit=service_unit,
    )

    # Then...
    assert adapter.get_contact_to_bill() == invoice.recipient
    assert invoice.recipient == original_contact


@pytest.mark.django_db
@pytest.mark.parametrize(
    # Pass the ID to the test setup fixture
    "invoice_sales_order_adapter_billing_contact_test_setup",
    [ServiceUnitId.MAKE, ServiceUnitId.KAMA],
    indirect=True,
)
def test_get_contact_to_bill_when_billing_contact_ends_but_another_billing_contact_covers_billing_period(
    invoice_sales_order_adapter_billing_contact_test_setup: dict[str, Any],
    tenant_factory: Callable[..., Tenant],
    tenant_contact_factory: Callable[..., TenantContact],
    contact_factory: Callable[..., Contact],
    invoice_factory: Callable[..., Invoice],
    invoice_row_factory: Callable[..., InvoiceRow],
):
    """
    Case: Billing contact is ended before the invoice's billing period.
          There is another billing contact.

    Given:
    - tenant contact (type=tenant),
    - billing contact (type=billing),
    - invoice for this billing contact,
    - invoice rows for this tenant,
    - billing period when the contacts are active,

    When:
    - billing contact ends before the invoice's billing period,
    - another billing contact covers the billing period,

    Then:
    - get_contact_to_bill() should return the active billing contact's contact,
      because they are the designated billing contact for the lease during the
      invoice's billing period.
    """
    # Given...
    lease: Lease = invoice_sales_order_adapter_billing_contact_test_setup["lease"]
    service_unit: ServiceUnit = invoice_sales_order_adapter_billing_contact_test_setup[
        "service_unit"
    ]

    tenant = tenant_factory(
        lease=lease,
        share_numerator=1,
        share_denominator=1,
        reference=None,
    )

    tenant_contacts_contact = contact_factory(first_name="Tenant", last_name="Contact")
    tenant_contact_factory(
        type=TenantContactType.TENANT,
        tenant=tenant,
        contact=tenant_contacts_contact,
        start_date=datetime.date(2026, 1, 1),
    )

    original_billing_person = contact_factory(
        first_name="Billing Original", last_name="Contact"
    )
    original_billing_contact = tenant_contact_factory(
        type=TenantContactType.BILLING,
        tenant=tenant,
        contact=original_billing_person,
        start_date=datetime.date(2026, 1, 1),
    )

    # Invoice for December 2026, originally issued to the active billing contact.
    billing_period_start_date = datetime.date(year=2026, month=12, day=1)
    billing_period_end_date = datetime.date(year=2026, month=12, day=31)

    invoice = invoice_factory(
        lease=lease,
        total_amount=Decimal("111.11"),
        billed_amount=Decimal("111.11"),
        outstanding_amount=Decimal("111.11"),
        recipient=original_billing_person,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
    )
    invoicerow_receivable_type: ReceivableType = (
        invoice_sales_order_adapter_billing_contact_test_setup[
            "invoicerow_receivable_type"
        ]
    )
    invoice_row_factory(
        invoice=invoice,
        tenant=tenant,
        receivable_type=invoicerow_receivable_type,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
        amount=Decimal("111.11"),
    )

    # When...
    # Original billing contact is ended before the billing period.
    original_billing_contact.end_date = datetime.date(2026, 11, 30)
    original_billing_contact.save()

    # A new billing contact is added that covers the billing period.
    new_billing_person = contact_factory(first_name="Billing New", last_name="Contact")
    tenant_contact_factory(
        type=TenantContactType.BILLING,
        tenant=tenant,
        contact=new_billing_person,
        start_date=datetime.date(2026, 12, 1),
    )

    sales_order = create_sales_order_with_laske_values(service_unit)
    adapter = invoice_sales_order_adapter_factory(
        invoice=invoice,
        sales_order=sales_order,
        service_unit=service_unit,
    )

    # Then...
    assert adapter.get_contact_to_bill() == new_billing_person


@pytest.mark.django_db
@pytest.mark.parametrize(
    # Pass the ID to the test setup fixture
    "invoice_sales_order_adapter_billing_contact_test_setup",
    [ServiceUnitId.MAKE, ServiceUnitId.KAMA],
    indirect=True,
)
def test_get_contact_to_bill_when_billing_contact_ends_but_tenant_contact_covers_billing_period(
    invoice_sales_order_adapter_billing_contact_test_setup: dict[str, Any],
    tenant_factory: Callable[..., Tenant],
    tenant_contact_factory: Callable[..., TenantContact],
    contact_factory: Callable[..., Contact],
    invoice_factory: Callable[..., Invoice],
    invoice_row_factory: Callable[..., InvoiceRow],
):
    """
    Case: Billing contact is ended before the invoice's billing period.
          No other billing contacts remain. Only the tenant contact remains.

    Given:
    - tenant contact (type=tenant),
    - billing contact (type=billing),
    - invoice for this billing contact,
    - invoice rows for this tenant,
    - billing period when the contacts are active,

    When:
    - billing contact ends before the invoice's billing period,
    - no active billing contacts remain,
    - active tenant contact remains,

    Then:
    - get_contact_to_bill() should return the tenant contact's contact,
      because they are the main responsible party for the lease during the
      invoice's billing period when no billing contacts are active.
    """
    # Given...
    lease: Lease = invoice_sales_order_adapter_billing_contact_test_setup["lease"]
    service_unit: ServiceUnit = invoice_sales_order_adapter_billing_contact_test_setup[
        "service_unit"
    ]

    tenant = tenant_factory(
        lease=lease,
        share_numerator=1,
        share_denominator=1,
        reference=None,
    )

    tenant_contacts_contact = contact_factory(first_name="Tenant", last_name="Contact")
    # Tenant contact: active throughout 2026 and beyond.
    tenant_contact_factory(
        type=TenantContactType.TENANT,
        tenant=tenant,
        contact=tenant_contacts_contact,
        start_date=datetime.date(2026, 1, 1),
    )

    original_billing_person = contact_factory(first_name="Billing", last_name="Contact")
    billing_contact = tenant_contact_factory(
        type=TenantContactType.BILLING,
        tenant=tenant,
        contact=original_billing_person,
        start_date=datetime.date(2026, 1, 1),
    )

    # Invoice for December 2026, originally issued to the active billing contact.
    billing_period_start_date = datetime.date(year=2026, month=12, day=1)
    billing_period_end_date = datetime.date(year=2026, month=12, day=31)

    invoice = invoice_factory(
        lease=lease,
        total_amount=Decimal("111.11"),
        billed_amount=Decimal("111.11"),
        outstanding_amount=Decimal("111.11"),
        recipient=original_billing_person,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
    )
    invoicerow_receivable_type: ReceivableType = (
        invoice_sales_order_adapter_billing_contact_test_setup[
            "invoicerow_receivable_type"
        ]
    )
    invoice_row_factory(
        invoice=invoice,
        tenant=tenant,
        receivable_type=invoicerow_receivable_type,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
        amount=Decimal("111.11"),
    )

    # When...
    # Billing contact is ended before the billing period; no new billing contact is added.
    billing_contact.end_date = datetime.date(2026, 11, 30)
    billing_contact.save()

    sales_order = create_sales_order_with_laske_values(service_unit)
    adapter = invoice_sales_order_adapter_factory(
        invoice=invoice,
        sales_order=sales_order,
        service_unit=service_unit,
    )

    # Then...
    # get_billing_tenantcontacts finds no billing contacts for Dec → falls back to tenant contacts.
    assert adapter.get_contact_to_bill() == tenant_contacts_contact


@pytest.mark.django_db
@pytest.mark.parametrize(
    # Pass the ID to the test setup fixture
    "invoice_sales_order_adapter_billing_contact_test_setup",
    [ServiceUnitId.MAKE, ServiceUnitId.KAMA],
    indirect=True,
)
def test_get_contact_to_bill_when_billing_contact_ends_and_no_other_contacts_exist(
    invoice_sales_order_adapter_billing_contact_test_setup: dict[str, Any],
    tenant_factory: Callable[..., Tenant],
    tenant_contact_factory: Callable[..., TenantContact],
    contact_factory: Callable[..., Contact],
    invoice_factory: Callable[..., Invoice],
    invoice_row_factory: Callable[..., InvoiceRow],
):
    """
    Case: Billing contact is ended before the invoice's billing period.
          No other billing contacts, or tenant contacts remain.

    Note: This should not happen intentionally, because there should always be at
    least one active tenant contact for the lease, but it is technically
    possible.

    Given:
    - tenant contact (type=tenant),
    - billing contact (type=billing),
    - invoice for this billing contact,
    - invoice rows for this tenant,
    - billing period when the contacts are active,

    When:
    - billing contact ends before the invoice's billing period,
    - no active billing contacts remain,
    - no active tenant contacts remain,

    Then:
    - get_contact_to_bill() should return the invoice's original recipient,
        because there are no other contacts to send the invoice to.

    """
    # Given...
    lease: Lease = invoice_sales_order_adapter_billing_contact_test_setup["lease"]
    service_unit: ServiceUnit = invoice_sales_order_adapter_billing_contact_test_setup[
        "service_unit"
    ]

    tenant = tenant_factory(
        lease=lease,
        share_numerator=1,
        share_denominator=1,
        reference=None,
    )

    tenant_contacts_contact = contact_factory(first_name="Tenant", last_name="Contact")
    tenant_contact = tenant_contact_factory(
        type=TenantContactType.TENANT,
        tenant=tenant,
        contact=tenant_contacts_contact,
        start_date=datetime.date(2026, 1, 1),
    )

    original_billing_person = contact_factory(first_name="Billing", last_name="Contact")
    billing_contact = tenant_contact_factory(
        type=TenantContactType.BILLING,
        tenant=tenant,
        contact=original_billing_person,
        start_date=datetime.date(2026, 1, 1),
    )

    # Invoice for December 2026, originally issued to the active billing contact.
    billing_period_start_date = datetime.date(year=2026, month=12, day=1)
    billing_period_end_date = datetime.date(year=2026, month=12, day=31)

    invoice = invoice_factory(
        lease=lease,
        total_amount=Decimal("111.11"),
        billed_amount=Decimal("111.11"),
        outstanding_amount=Decimal("111.11"),
        recipient=original_billing_person,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
    )
    invoicerow_receivable_type: ReceivableType = (
        invoice_sales_order_adapter_billing_contact_test_setup[
            "invoicerow_receivable_type"
        ]
    )
    invoice_row_factory(
        invoice=invoice,
        tenant=tenant,
        receivable_type=invoicerow_receivable_type,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
        amount=Decimal("111.11"),
    )

    # When...
    # Both billing and tenant contacts are ended before the billing period.
    billing_contact.end_date = datetime.date(2026, 11, 30)
    billing_contact.save()
    tenant_contact.end_date = datetime.date(2026, 11, 30)
    tenant_contact.save()

    sales_order = create_sales_order_with_laske_values(service_unit)
    adapter = invoice_sales_order_adapter_factory(
        invoice=invoice,
        sales_order=sales_order,
        service_unit=service_unit,
    )

    # Then...
    # get_billing_tenantcontacts finds no billing contacts → falls back to tenant contacts → also none.
    # Falls through to invoice.recipient.
    assert adapter.get_contact_to_bill() == invoice.recipient
    assert invoice.recipient == original_billing_person


@pytest.mark.django_db
@pytest.mark.parametrize(
    # Pass the ID to the test setup fixture
    "invoice_sales_order_adapter_billing_contact_test_setup",
    [ServiceUnitId.MAKE, ServiceUnitId.KAMA],
    indirect=True,
)
def test_get_contact_to_bill_when_newer_billing_contact_covers_billing_period_and_another_begins_midway(
    invoice_sales_order_adapter_billing_contact_test_setup: dict[str, Any],
    tenant_factory: Callable[..., Tenant],
    tenant_contact_factory: Callable[..., TenantContact],
    contact_factory: Callable[..., Contact],
    invoice_factory: Callable[..., Invoice],
    invoice_row_factory: Callable[..., InvoiceRow],
):
    """
    Case: Billing contact covers the entire billing period, but another billing
    contact begins midway through the invoice's billing period.

    Given:
    - tenant contact (type=tenant),
    - billing contact (type=billing),
    - invoice for this contact,
    - invoice rows for this tenant,
    - billing period when the contacts are active,

    When:
    - billing contact covers the billing period,
    - another billing contact begins midway through the invoice's billing period,

    Then:
    - get_contact_to_bill() should return the newer billing contact's contact,
      because it is responsible for part of the invoice's billing period, and
      newer contacts are preferred over older contacts.
    """
    # Given...
    lease: Lease = invoice_sales_order_adapter_billing_contact_test_setup["lease"]
    service_unit: ServiceUnit = invoice_sales_order_adapter_billing_contact_test_setup[
        "service_unit"
    ]

    tenant = tenant_factory(
        lease=lease,
        share_numerator=1,
        share_denominator=1,
        reference=None,
    )

    tenant_contacts_contact = contact_factory(first_name="Tenant", last_name="Contact")
    tenant_contact_factory(
        type=TenantContactType.TENANT,
        tenant=tenant,
        contact=tenant_contacts_contact,
        start_date=datetime.date(2026, 1, 1),
    )

    older_billing_person = contact_factory(
        first_name="Billing Older", last_name="Contact"
    )
    # Billing contact at invoice creation time: active from Jan 1, no end date.
    tenant_contact_factory(
        type=TenantContactType.BILLING,
        tenant=tenant,
        contact=older_billing_person,
        start_date=datetime.date(2026, 1, 1),
    )

    # Invoice for December 2026, originally issued to the active billing contact.
    billing_period_start_date = datetime.date(year=2026, month=12, day=1)
    billing_period_end_date = datetime.date(year=2026, month=12, day=31)

    invoice = invoice_factory(
        lease=lease,
        total_amount=Decimal("111.11"),
        billed_amount=Decimal("111.11"),
        outstanding_amount=Decimal("111.11"),
        recipient=older_billing_person,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
    )
    invoicerow_receivable_type: ReceivableType = (
        invoice_sales_order_adapter_billing_contact_test_setup[
            "invoicerow_receivable_type"
        ]
    )
    invoice_row_factory(
        invoice=invoice,
        tenant=tenant,
        receivable_type=invoicerow_receivable_type,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
        amount=Decimal("111.11"),
    )

    # When...
    # A newer billing contact is added that starts midway through the billing period.
    newer_billing_person = contact_factory(
        first_name="Billing Newer", last_name="Contact"
    )
    tenant_contact_factory(
        type=TenantContactType.BILLING,
        tenant=tenant,
        contact=newer_billing_person,
        start_date=datetime.date(2026, 12, 15),
    )

    sales_order = create_sales_order_with_laske_values(service_unit)
    adapter = invoice_sales_order_adapter_factory(
        invoice=invoice,
        sales_order=sales_order,
        service_unit=service_unit,
    )

    # Then...
    # get_billing_tenantcontacts returns both, ordered by -start_date → newer (Dec 15) is first.
    assert adapter.get_contact_to_bill() == newer_billing_person


@pytest.mark.django_db
@pytest.mark.parametrize(
    # Pass the ID to the test setup fixture
    "invoice_sales_order_adapter_billing_contact_test_setup",
    [ServiceUnitId.MAKE, ServiceUnitId.KAMA],
    indirect=True,
)
def test_get_contact_to_bill_when_billing_contact_ends_during_billing_period_and_another_begins(
    invoice_sales_order_adapter_billing_contact_test_setup: dict[str, Any],
    tenant_factory: Callable[..., Tenant],
    tenant_contact_factory: Callable[..., TenantContact],
    contact_factory: Callable[..., Contact],
    invoice_factory: Callable[..., Invoice],
    invoice_row_factory: Callable[..., InvoiceRow],
):
    """
    Case: Billing contact ends during the invoice's billing period, but another billing contact begins.

    Given:
    - tenant contact (type=tenant),
    - billing contact (type=billing),
    - invoice for this contact,
    - invoice rows for this tenant,
    - billing period when the contacts are active,

    When:
    - billing contact ends during the invoice's billing period,
    - another billing contact begins,

    Then:
    - get_contact_to_bill() should return the newer billing contact's contact,
      because it is responsible for part of the invoice's billing period, and
      newer contacts are preferred over older contacts.
    """
    # Given...
    lease: Lease = invoice_sales_order_adapter_billing_contact_test_setup["lease"]
    service_unit: ServiceUnit = invoice_sales_order_adapter_billing_contact_test_setup[
        "service_unit"
    ]

    tenant = tenant_factory(
        lease=lease,
        share_numerator=1,
        share_denominator=1,
        reference=None,
    )

    tenant_contacts_contact = contact_factory(first_name="Tenant", last_name="Contact")
    tenant_contact_factory(
        type=TenantContactType.TENANT,
        tenant=tenant,
        contact=tenant_contacts_contact,
        start_date=datetime.date(2026, 1, 1),
    )

    original_billing_person = contact_factory(
        first_name="Billing Original", last_name="Contact"
    )
    # Billing contact at invoice creation time: active from Jan 1, no end date.
    original_billing_contact = tenant_contact_factory(
        type=TenantContactType.BILLING,
        tenant=tenant,
        contact=original_billing_person,
        start_date=datetime.date(2026, 1, 1),
    )

    # Invoice for December 2026, originally issued to the active billing contact.
    billing_period_start_date = datetime.date(year=2026, month=12, day=1)
    billing_period_end_date = datetime.date(year=2026, month=12, day=31)

    invoice = invoice_factory(
        lease=lease,
        total_amount=Decimal("111.11"),
        billed_amount=Decimal("111.11"),
        outstanding_amount=Decimal("111.11"),
        recipient=original_billing_person,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
    )
    invoicerow_receivable_type: ReceivableType = (
        invoice_sales_order_adapter_billing_contact_test_setup[
            "invoicerow_receivable_type"
        ]
    )
    invoice_row_factory(
        invoice=invoice,
        tenant=tenant,
        receivable_type=invoicerow_receivable_type,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
        amount=Decimal("111.11"),
    )

    # When...
    # Original billing contact ends mid-period; a newer billing contact picks up immediately.
    original_billing_contact.end_date = datetime.date(2026, 12, 15)
    original_billing_contact.save()

    newer_billing_person = contact_factory(
        first_name="Billing Newer", last_name="Contact"
    )
    tenant_contact_factory(
        type=TenantContactType.BILLING,
        tenant=tenant,
        contact=newer_billing_person,
        start_date=datetime.date(2026, 12, 16),
    )

    sales_order = create_sales_order_with_laske_values(service_unit)
    adapter = invoice_sales_order_adapter_factory(
        invoice=invoice,
        sales_order=sales_order,
        service_unit=service_unit,
    )

    # Then...
    # Both billing contacts overlap the Dec period; ordered by -start_date → newer (Dec 16) is first.
    assert adapter.get_contact_to_bill() == newer_billing_person


@pytest.mark.django_db
@pytest.mark.parametrize(
    # Pass the ID to the test setup fixture
    "invoice_sales_order_adapter_billing_contact_test_setup",
    [ServiceUnitId.MAKE, ServiceUnitId.KAMA],
    indirect=True,
)
def test_get_contact_to_bill_when_billing_contact_ends_during_billing_period_and_only_tenant_contact_remains(
    invoice_sales_order_adapter_billing_contact_test_setup: dict[str, Any],
    tenant_factory: Callable[..., Tenant],
    tenant_contact_factory: Callable[..., TenantContact],
    contact_factory: Callable[..., Contact],
    invoice_factory: Callable[..., Invoice],
    invoice_row_factory: Callable[..., InvoiceRow],
):
    """
    Case: Billing contact ends during the invoice's billing period.
          No other billing contacts remain. Only the tenant contact remains.

    Given:
    - tenant contact (type=tenant),
    - billing contact (type=billing),
    - invoice for this contact,
    - invoice rows for this tenant,
    - billing period when the contacts are active,

    When:
    - billing contact ends during the invoice's billing period,
    - no other billing contacts remain,
    - active tenant contact remains,

    Then:
    - get_contact_to_bill() should return the tenant contact's contact,
      because the expired billing contact might not want to receive the invoices
      from period when they are only partially responsible.
      The tenant contact is the main responsible party for the lease during the
      invoice's billing period.
    """
    # Given...
    lease: Lease = invoice_sales_order_adapter_billing_contact_test_setup["lease"]
    service_unit: ServiceUnit = invoice_sales_order_adapter_billing_contact_test_setup[
        "service_unit"
    ]

    tenant = tenant_factory(
        lease=lease,
        share_numerator=1,
        share_denominator=1,
        reference=None,
    )

    tenant_contacts_contact = contact_factory(first_name="Tenant", last_name="Contact")
    # Tenant contact: active throughout the billing period.
    tenant_contact_factory(
        type=TenantContactType.TENANT,
        tenant=tenant,
        contact=tenant_contacts_contact,
        start_date=datetime.date(2026, 1, 1),
    )

    billing_contact_person = contact_factory(first_name="Billing", last_name="Contact")
    # Billing contact at invoice creation time: active from Jan 1, no end date.
    billing_contact = tenant_contact_factory(
        type=TenantContactType.BILLING,
        tenant=tenant,
        contact=billing_contact_person,
        start_date=datetime.date(2026, 1, 1),
    )

    # Invoice for December 2026, originally issued to the active billing contact.
    billing_period_start_date = datetime.date(year=2026, month=12, day=1)
    billing_period_end_date = datetime.date(year=2026, month=12, day=31)

    invoice = invoice_factory(
        lease=lease,
        total_amount=Decimal("111.11"),
        billed_amount=Decimal("111.11"),
        outstanding_amount=Decimal("111.11"),
        recipient=billing_contact_person,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
    )
    invoicerow_receivable_type: ReceivableType = (
        invoice_sales_order_adapter_billing_contact_test_setup[
            "invoicerow_receivable_type"
        ]
    )
    invoice_row_factory(
        invoice=invoice,
        tenant=tenant,
        receivable_type=invoicerow_receivable_type,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
        amount=Decimal("111.11"),
    )

    # When...
    # Billing contact ends mid-period; no replacement is added.
    billing_contact.end_date = datetime.date(2026, 12, 15)
    billing_contact.save()

    sales_order = create_sales_order_with_laske_values(service_unit)
    adapter = invoice_sales_order_adapter_factory(
        invoice=invoice,
        sales_order=sales_order,
        service_unit=service_unit,
    )

    # Then...
    assert adapter.get_contact_to_bill() == tenant_contacts_contact
