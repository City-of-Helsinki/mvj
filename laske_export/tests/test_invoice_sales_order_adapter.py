from decimal import Decimal
from typing import Any

import pytest

from laske_export.document.invoice_sales_order_adapter import (
    InvoiceSalesOrderAdapter,
    _sort_invoice_rows_for_lineitems,
)
from laske_export.document.sales_order import LineItem
from leasing.enums import ServiceUnitId
from leasing.models.invoice import Invoice, InvoiceRow
from leasing.models.lease import Lease, LeaseType
from leasing.models.receivable_type import ReceivableType
from leasing.models.service_unit import ServiceUnit


@pytest.mark.parametrize(
    # Pass the ID to the test setup fixture
    "exporter_lacking_test_setup",
    [ServiceUnitId.AKV],
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
    [ServiceUnitId.AKV],
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
    [ServiceUnitId.AKV],
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
    [ServiceUnitId.MAKE, ServiceUnitId.AKV],
    indirect=True,
)
@pytest.mark.django_db
def test_get_sorted_invoice_rows(exporter_full_test_setup: dict[str, Any]):
    """Test that invoice rows are properly sorted by amount."""
    invoice: Invoice = exporter_full_test_setup["invoice1"]
    InvoiceRow.objects.all().filter(invoice_id=invoice.id).delete()
    assert InvoiceRow.objects.count() == 0

    receivable_type = exporter_full_test_setup["invoicerow1_receivable_type"]

    row1 = InvoiceRow.objects.create(
        invoice=invoice,
        amount=Decimal("100.00"),
        receivable_type=receivable_type,
    )
    row2 = InvoiceRow.objects.create(
        invoice=invoice,
        amount=Decimal("-0.01"),
        receivable_type=receivable_type,
    )
    row3 = InvoiceRow.objects.create(
        invoice=invoice,
        amount=Decimal("-25.00"),
        receivable_type=receivable_type,
    )
    row4 = InvoiceRow.objects.create(
        invoice=invoice,
        amount=Decimal("0.05"),
        receivable_type=receivable_type,
    )
    row5 = InvoiceRow.objects.create(
        invoice=invoice,
        amount=Decimal("200.00"),
        receivable_type=receivable_type,
    )
    row6 = InvoiceRow.objects.create(
        invoice=invoice,
        amount=Decimal("-50.00"),
        receivable_type=receivable_type,
    )

    # Get sorted rows
    sorted_rows = _sort_invoice_rows_for_lineitems(invoice.rows.all())

    # Expected order:
    # 1. Charges (positive amounts) in descending order: 200, 100
    # 2. Credits (negative amounts) in descending absolute order: -50, -25
    # 3. Roundings (small amounts) in descending order: 0.05, -0.01
    expected_order = [
        row5,
        row1,
        row6,
        row3,
        row4,
        row2,
    ]

    assert len(sorted_rows) == 6
    assert sorted_rows == expected_order
