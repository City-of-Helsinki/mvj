from decimal import Decimal
from typing import Any, Callable

import pytest

from laske_export.document.invoice_sales_order_adapter import (
    InvoiceSalesOrderAdapter,
)
from laske_export.document.sales_order import LineItem
from leasing.enums import InvoiceRowType, ServiceUnitId
from leasing.models.invoice import Invoice, InvoiceRow
from leasing.models.lease import IntendedUse, Lease, LeaseType
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
    # Parametrize service unit ID, and pass it to the test setup fixture,
    # to properly initialize the data necessary for invoicing to work,
    # and ensure this test covers every service unit.
    "exporter_full_test_setup",
    [unit_id for unit_id in list(ServiceUnitId)],
    indirect=True,
)
@pytest.mark.parametrize(
    "row_ordering_by_type",
    [
        [InvoiceRowType.ROUNDING, InvoiceRowType.CREDIT, InvoiceRowType.CHARGE],
        [InvoiceRowType.ROUNDING, InvoiceRowType.CHARGE, InvoiceRowType.CREDIT],
        [InvoiceRowType.CREDIT, InvoiceRowType.ROUNDING, InvoiceRowType.CHARGE],
        [InvoiceRowType.CREDIT, InvoiceRowType.CHARGE, InvoiceRowType.ROUNDING],
        [
            InvoiceRowType.ROUNDING,
            InvoiceRowType.CREDIT,
            InvoiceRowType.CHARGE,
            InvoiceRowType.CREDIT,
            InvoiceRowType.CREDIT,
            InvoiceRowType.ROUNDING,
            InvoiceRowType.CHARGE,
        ],
    ],
)
@pytest.mark.django_db
def test_invoice_row_ordering(
    exporter_full_test_setup: dict[str, Any],
    invoice_row_factory: Callable[..., InvoiceRow],
    row_ordering_by_type: list[InvoiceRowType],
):
    """LineItem ordering should align with the expected InvoiceRow ordering"""
    invoice1: Invoice = exporter_full_test_setup["invoice1"]
    adapter = exporter_full_test_setup["adapter"]

    receivable_type: ReceivableType = exporter_full_test_setup[
        "invoicerow1_receivable_type"
    ]
    intended_use: IntendedUse = exporter_full_test_setup["invoicerow1_intended_use"]

    # get rid of the pre-created invoicerow that could affect results
    row_charge_old: InvoiceRow = exporter_full_test_setup["invoicerow1"]
    row_charge_old.delete()
    assert invoice1.rows.count() == 0

    row_type_to_amount = {
        InvoiceRowType.CHARGE: Decimal("100.00"),
        InvoiceRowType.CREDIT: Decimal("-100"),
        InvoiceRowType.ROUNDING: Decimal("0.01"),
    }
    for i, row_type in enumerate(row_ordering_by_type):
        invoice_row_factory(
            invoice=invoice1,
            receivable_type=receivable_type,
            intended_use=intended_use,
            amount=row_type_to_amount[row_type],
            type=row_type,
        )

    adapter.invoice = invoice1
    line_items = adapter.get_line_items()

    assert len(line_items) == len(row_ordering_by_type)
    assert len(line_items) == invoice1.rows.count()

    required_order = InvoiceRow.get_type_ordering_priority()

    # Verify that line items are in the required order based on invoicerow type,
    # no matter how many rows per type are added.
    row_types = []
    for item in line_items:
        # Match the item to the invoicerow based on row's amount and item's net price,
        # because all rows of same type have the same amount, in this test.
        item_amount = Decimal(item.net_price.replace(",", "."))
        row = invoice1.rows.filter(amount=item_amount).first()

        # The type must be known in the ordering, otherwise the ordering should
        # be updated.
        assert row.type in required_order

        row_types.append(row.type)

    # Compare each row's type to the next
    for type1, type2 in zip(row_types, row_types[1:]):
        if type1 == type2:
            # No ordering required between rows of same type
            continue
        else:
            assert required_order.index(type1) < required_order.index(type2)
