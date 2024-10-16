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

    # Extract the results from initialized objects
    invoicerow_intended_use = akv_default_test_setup["invoicerow1_intended_use"]
    lease_area_m2 = str(akv_default_test_setup["lease_area1"].area)
    district = akv_default_test_setup["district"]
    primary_lease_area_address = akv_default_test_setup["lease_area1_address2"]
    decision = akv_default_test_setup["decision"]
    billing_period_start_date = akv_default_test_setup[
        "invoice1_billing_period_start_date"
    ]
    billing_period_end_date = akv_default_test_setup["invoice1_billing_period_end_date"]
    date_format = AkvInvoiceSalesOrderAdapter.AKV_DATE_FORMAT

    combined_linetext = get_combined_linetext_from_adapter(adapter)

    # Verify that requirements match
    assert invoicerow_intended_use.name in combined_linetext
    assert lease_area_m2 in combined_linetext
    assert district.name in combined_linetext
    assert district.identifier in combined_linetext
    assert primary_lease_area_address.address in combined_linetext
    assert primary_lease_area_address.postal_code in combined_linetext
    assert decision.reference_number in combined_linetext
    assert decision.decision_date.strftime(date_format) in combined_linetext
    assert decision.section in combined_linetext
    assert billing_period_start_date.strftime(date_format) in combined_linetext
    assert billing_period_end_date.strftime(date_format) in combined_linetext


@pytest.mark.django_db
def test_missing_sections_not_added(
    django_db_setup,
    akv_lacking_test_setup,
    lease_area_factory,
):
    """
    Verify that invoicerow lineitem linetext doesn't contain sections that have
    missing details in the input data, such as lease area, or missing decision.

    This cleanup of text with missing sections is for corner cases.
    The actual invoices are expected to contain all necessary details.
    """
    adapter = akv_lacking_test_setup["adapter"]
    linetext_without_area = get_combined_linetext_from_adapter(adapter)

    # Lease area is missing
    assert "m²" not in linetext_without_area

    # Create a lease area, so that it exists in the next asserts
    lease_area_factory(
        lease=akv_lacking_test_setup["lease"],
        area=100,
        archived_decision=None,
    )
    adapter.set_values()
    linetext_without_decision = get_combined_linetext_from_adapter(adapter)
    assert "m²" in linetext_without_decision

    # Decision is missing
    assert "Päätös" not in linetext_without_decision
    assert "§" not in linetext_without_decision

    # Maybe no need to test other implementation details here.
    # The actual invoices should contain all necessary items for a full linetext.


def get_combined_linetext_from_adapter(adapter: AkvInvoiceSalesOrderAdapter) -> str:
    """Combines the linetext from all line_text_l<number> lines to a single string."""
    line_item = adapter.sales_order.line_items[0]
    line_texts = []
    for i in range(1, 7):
        line_texts.append(getattr(line_item, f"line_text_l{i}", ""))

    return "".join(line_texts)
