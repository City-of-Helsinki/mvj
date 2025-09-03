import pytest
from constance.test import override_config

from leasing.enums import ServiceUnitId
from leasing.tests.conftest import *  # noqa

from .conftest import get_exported_file_as_tree


@pytest.mark.parametrize(
    # Pass the ID to test setup fixture
    "exporter_full_test_setup",
    [ServiceUnitId.AKV],
    indirect=True,
)
@pytest.mark.django_db
@override_config(LASKE_EXPORT_ANNOUNCE_EMAIL=None)
def test_akv_xml_elements_exist(
    settings,
    monkeypatch_laske_exporter_send,
    send_invoices_to_laske_command,
    exporter_full_test_setup,
):
    """
    Sanity check: verify that the necessary XML elements are populated in AKV's
    export XML, no matter what value.

    Note: this might not be all. If you find out more mandatory fields that are
    expected to be populated in every XML export, please add to this test.
    """
    command = send_invoices_to_laske_command
    command.handle(service_unit_id=ServiceUnitId.AKV)

    xml_tree = get_exported_file_as_tree(settings)
    sales_order = xml_tree.find("./SBO_SalesOrder")

    assert sales_order.find("SenderId").text is not None
    assert sales_order.find("Reference").text is not None
    assert sales_order.find("OrderType").text is not None
    assert sales_order.find("SalesOrg").text is not None
    assert sales_order.find("DistributionChannel").text is not None
    assert sales_order.find("Division").text is not None
    assert sales_order.find("SalesOffice").text is not None
    assert sales_order.find("PMNTTERM").text is not None
    assert sales_order.find("ReferenceText").text is not None
    assert sales_order.find("BillingDate").text is not None

    line_item = xml_tree.find("./SBO_SalesOrder/LineItem")
    assert line_item.find("Material").text is not None
    assert line_item.find("Quantity").text is not None
    assert line_item.find("NetPrice").text is not None
    assert line_item.find("LineTextL1").text is not None
    # Note: some linetexts might be None, depending on length of the contents
    assert (
        line_item.find("WBS_Element") is not None  # sap_project_number
        or line_item.find("OrderItemNumber").text is not None
        or line_item.find("ProfitCenter").text is not None
    )


@pytest.mark.parametrize(
    # Pass the ID to test setup fixture
    "exporter_full_test_setup",
    [ServiceUnitId.AKV],
    indirect=True,
)
@pytest.mark.django_db
@override_config(LASKE_EXPORT_ANNOUNCE_EMAIL=None)
def test_akv_sap_codes_from_invoicerow(
    settings,
    monkeypatch_laske_exporter_send,
    send_invoices_to_laske_command,
    exporter_full_test_setup,
):
    """
    By default, AKV SAP codes should be added to the line item from invoicerow's
    receivable type.
    """
    command = send_invoices_to_laske_command
    command.handle(service_unit_id=ServiceUnitId.AKV)

    xml_tree = get_exported_file_as_tree(settings)
    line_item = xml_tree.find("./SBO_SalesOrder/LineItem")

    assert (
        line_item.find("Material").text
        == exporter_full_test_setup["invoicerow1"].receivable_type.sap_material_code
    )
    assert (
        line_item.find("WBS_Element").text
        == exporter_full_test_setup["invoicerow1"].receivable_type.sap_project_number
    )


@pytest.mark.parametrize(
    # Pass the ID to test setup fixture
    "exporter_full_test_setup",
    [ServiceUnitId.AKV],
    indirect=True,
)
@pytest.mark.django_db
@override_config(LASKE_EXPORT_ANNOUNCE_EMAIL=None)
def test_akv_sap_codes_from_leasetype(
    monkeypatch_laske_exporter_send,
    settings,
    send_invoices_to_laske_command,
    exporter_full_test_setup,
    receivable_type_factory,
):
    """
    AKV SAP codes should be added to the line item from LeaseType when the
    invoicerow's receivable type is the service unit's default receivable type
    for rents, and that default doesn't have its own SAP codes.
    """
    service_unit = exporter_full_test_setup["service_unit"]

    invoice_row = exporter_full_test_setup["invoicerow1"]
    invoice_row.receivable_type = service_unit.default_receivable_type_rent
    invoice_row.save()

    command = send_invoices_to_laske_command
    command.handle(service_unit_id=ServiceUnitId.AKV)

    xml_tree = get_exported_file_as_tree(settings)
    line_item = xml_tree.find("./SBO_SalesOrder/LineItem")

    assert (
        line_item.find("Material").text
        == exporter_full_test_setup["lease"].type.sap_material_code
    )
    assert (
        line_item.find("WBS_Element").text
        == exporter_full_test_setup["lease"].type.sap_project_number
    )


@pytest.mark.parametrize(
    # Pass the ID to test setup fixture
    "exporter_full_test_setup",
    [ServiceUnitId.AKV],
    indirect=True,
)
@pytest.mark.django_db
@override_config(LASKE_EXPORT_ANNOUNCE_EMAIL=None)
def test_akv_sap_codes_when_collateral(
    monkeypatch_laske_exporter_send,
    settings,
    send_invoices_to_laske_command,
    exporter_full_test_setup,
):
    """
    AKV SAP codes should be added to the line item from invoicerow's receivable
    type when when invoicerow's receivable type is the service unit's default
    receivable type for collateral.

    Additionally, order item number should be added to the ProfitCenter element instead
    of the usual OrderItemNumber element.
    """
    service_unit = exporter_full_test_setup["service_unit"]

    invoice_row = exporter_full_test_setup["invoicerow1"]
    invoice_row.receivable_type = service_unit.default_receivable_type_collateral
    invoice_row.save()

    command = send_invoices_to_laske_command
    command.handle(service_unit_id=ServiceUnitId.AKV)

    xml_tree = get_exported_file_as_tree(settings)
    line_item = xml_tree.find("./SBO_SalesOrder/LineItem")

    assert (
        line_item.find("Material").text
        == exporter_full_test_setup["invoicerow1"].receivable_type.sap_material_code
    )
    assert (
        line_item.find("WBS_Element").text
        == exporter_full_test_setup["invoicerow1"].receivable_type.sap_project_number
    )
