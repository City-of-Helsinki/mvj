import pytest

from laske_export.document.invoice_sales_order_adapter import (
    AkvInvoiceSalesOrderAdapter,
)
from laske_export.document.sales_order import LineItem
from leasing.models.invoice import InvoiceRow
from leasing.models.receivable_type import ReceivableType


@pytest.mark.django_db
def test_set_line_item_common_values_sap(akv_lacking_test_setup):
    """Verifies that only one of 'wbs_element' and 'order_item_number' is set.
    If 'sap_project_number' is set, it should be set to 'wbs_element'.
    When 'sap_project_number' is set, 'sap_order_item_number' should be ignored.
    Otherwise, 'sap_order_item_number' should be set to 'order_item_number'.
    """
    adapter: AkvInvoiceSalesOrderAdapter = akv_lacking_test_setup["adapter"]
    invoice_row: InvoiceRow = akv_lacking_test_setup["invoicerow1"]
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
