import pytest

from laske_export.document.invoice_sales_order_adapter import (
    AkvInvoiceSalesOrderAdapter,
)


@pytest.mark.django_db
def test_akv_line_text(
    django_db_setup,
    akv_default_test_setup,
):
    """
    Verify that invoicerow lineitem linetext contains all details
    requested by AKV when invoice's service unit is AKV.
    """
    # Set up the values
    adapter = akv_default_test_setup["adapter"]

    # Extract the results from adapter
    line_item = adapter.sales_order.line_items[0]
    line_texts = []
    for i in range(1, 7):
        line_texts.append(getattr(line_item, f"line_text_l{i}", ""))

    date_format = AkvInvoiceSalesOrderAdapter.AKV_DATE_FORMAT
    combined_line_text = "".join(line_texts)

    invoicerow_intended_use = akv_default_test_setup["invoicerow1_intended_use"]
    lease_area_m2 = str(akv_default_test_setup["lease_area1"].area)
    district = akv_default_test_setup["district"]
    primary_lease_area_address = akv_default_test_setup["lease_area1_address2"]
    decision = akv_default_test_setup["decision"]
    billing_period_start_date = akv_default_test_setup[
        "invoice1_billing_period_start_date"
    ]
    billing_period_end_date = akv_default_test_setup["invoice1_billing_period_end_date"]

    # Verify that requirements match
    assert invoicerow_intended_use.name in combined_line_text
    assert lease_area_m2 in combined_line_text
    assert district.name in combined_line_text
    assert district.identifier in combined_line_text
    assert primary_lease_area_address.address in combined_line_text
    assert primary_lease_area_address.postal_code in combined_line_text
    assert decision.reference_number in combined_line_text
    assert decision.decision_date.strftime(date_format) in combined_line_text
    assert decision.section in combined_line_text
    assert billing_period_start_date.strftime(date_format) in combined_line_text
    assert billing_period_end_date.strftime(date_format) in combined_line_text
