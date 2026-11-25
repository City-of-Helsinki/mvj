import logging
from datetime import date
from decimal import Decimal
from unittest.mock import patch
from xml.etree import ElementTree

import pytest
from dateutil.relativedelta import relativedelta
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.utils import timezone

from landuse.models.agreement import LandUseAgreement
from landuse.models.invoice import (
    Invoice,
    InvoiceItem,
    InvoiceItemType,
    InvoiceStatus,
    InvoiceType,
)
from landuse.models.party import AgreementParty, BillingDetails
from laske_export.landuse import invoice_context
from laske_export.landuse.invoice_context import (
    render_invoices_xml,
    render_single_invoice_xml,
)
from laske_export.models import LanduseInvoiceExportLog


def test_wrap_sap_text_wraps_pads_and_warns_on_overflow(caplog):
    caplog.set_level(logging.WARNING, logger="laske_export.landuse.invoice_context")
    wrapped = invoice_context._wrap_sap_text(
        "one two three", line_length=5, line_count=4
    )

    assert wrapped == ("one ", "two ", "three", "")
    assert not caplog.text

    caplog.clear()
    wrapped = invoice_context._wrap_sap_text(
        "one two three", line_length=5, line_count=2
    )
    assert wrapped == ("one ", "two ")
    assert "SAP text exceeds the 2-line limit; omitting 1 wrapped lines." in caplog.text

    caplog.clear()
    wrapped = invoice_context._wrap_sap_text("abcdefghij", line_length=5, line_count=2)
    assert wrapped == ("abcde", "fghij")
    assert "abcdefghij" == "".join(wrapped)
    assert not caplog.text

    caplog.clear()
    wrapped = invoice_context._wrap_sap_text("abcdefghijk", line_length=5, line_count=2)
    assert wrapped == ("abcde", "fghij")
    assert "abcdefghijk" != "".join(wrapped)
    assert "SAP text exceeds the 2-line limit; omitting 1 wrapped lines." in caplog.text


@pytest.fixture
def invoice(db, settings) -> Invoice:
    settings.SAP_LANDUSE_VALUES = {
        "sender_id": "ID990",
        "sales_org": "9999",
        "sales_office": "9000",
        "distribution_channel": "90",
        "division": "90",
        "pmntterm": "Z900",
    }
    agreement = LandUseAgreement.objects.create(identifier="M-2026-1")
    recipient = AgreementParty.objects.create(
        agreement=agreement,
        name="Example & Sons",
        business_id="1234567-8",
        street_address="Main street 1",
        postal_code="00100",
        city="Helsinki",
    )
    BillingDetails.objects.create(
        agreement_party=recipient,
        ovt_code="003712345678",
        sap_customer_number="1000123",
        customer_reference="Customer reference",
    )
    return Invoice.objects.create(
        agreement=agreement,
        recipient_party=recipient,
        installment_sequence_number=1,
        installment_count_total=2,
        due_date=date(2026, 10, 31),
        invoice_type=InvoiceType.LAND_USE_COMPENSATION,
        billed_amount=Decimal("1250.50"),
    )


@pytest.mark.django_db
@patch("laske_export.landuse_export.send_invoices_xml")
def test_invoice_xml_is_generated_only_when_sent(send_invoices_xml, invoice: Invoice):
    assert invoice.sap_xml is None

    invoice.status = InvoiceStatus.WAITING_TO_BE_SENT
    invoice.due_date = timezone.localdate()
    invoice.save()
    assert invoice.sap_xml is None

    call_command("send_landuse_invoices")
    invoice.refresh_from_db()

    root = ElementTree.fromstring(invoice.sap_xml or "")
    sales_order = root.find("SBO_SalesOrder")

    assert root.tag == "SBO_SalesOrderContainer"
    assert sales_order is not None
    assert sales_order.findtext("SenderId") == "ID990"
    assert sales_order.findtext("Reference") == str(invoice.invoice_identifier)
    assert sales_order.findtext("ContractNumber") == "M-2026-1"
    assert sales_order.findtext("OrderType") == "ZTY1"
    assert sales_order.findtext("BillingDate") == invoice.due_date.strftime("%Y%m%d")
    assert sales_order.findtext("OrderParty/PriorityName1") == "Example & Sons"
    assert sales_order.findtext("OrderParty/SAPCustomerID") == "1000123"
    assert sales_order.findtext("BillingParty1/CustomerOVT") == "003712345678"
    assert invoice.sent_at is not None
    assert invoice.status == InvoiceStatus.OPEN
    send_invoices_xml.assert_called_once_with(
        LanduseInvoiceExportLog.objects.get().pk, invoice.sap_xml
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "description",
    [
        "Land-use compensation",
        'Compensation & interest <2026> "quoted"',
        "Korvaus \u00e4\u00f6\u00e5",
    ],
)
def test_invoice_generation_creates_valid_xml(invoice: Invoice, description):
    InvoiceItem.objects.create(
        invoice=invoice,
        item_type=InvoiceItemType.LAND_USE_COMPENSATION,
        description=description,
        amount=Decimal("1250.50"),
    )

    xml = render_single_invoice_xml(invoice)

    # Would raise ElementTree.ParseError if not valid XML
    root = ElementTree.fromstring(xml.encode("utf-8"))

    assert xml.startswith('<?xml version="1.0" encoding="UTF-8"?>')
    assert root.tag == "SBO_SalesOrderContainer"
    assert len(root) == 1
    sales_order = root[0]
    assert sales_order.tag == "SBO_SalesOrder"
    assert sales_order.findtext("Reference") == str(invoice.invoice_identifier)
    assert sales_order.findtext("OrderParty/PriorityName1") == "Example & Sons"
    assert len(sales_order.findall("LineItem")) == 1
    assert sales_order.findtext("LineItem/LineTextL1") == description
    assert sales_order.findtext("LineItem/Quantity") == "1,00"
    assert sales_order.findtext("LineItem/NetPrice") == "1250,50"


@pytest.mark.django_db
def test_party_name_is_wrapped_into_priority_and_info_name_lines(invoice: Invoice):
    long_name = "A" * 120
    snapshot = invoice.recipient_snapshot
    snapshot.name = long_name
    snapshot.save(update_fields=["name"])

    xml = render_single_invoice_xml(invoice)
    sales_order = ElementTree.fromstring(xml).find("SBO_SalesOrder")
    expected_lines = [long_name[index : index + 35] for index in range(0, 120, 35)]

    for party_name in ("OrderParty", "BillingParty1"):
        priority_names = [
            sales_order.findtext(f"{party_name}/PriorityName{number}")
            for number in range(1, 5)
        ]
        info_names = [
            sales_order.findtext(f"{party_name}/InfoName{number}")
            for number in range(1, 5)
        ]
        assert priority_names == expected_lines
        assert info_names == expected_lines


@pytest.mark.django_db
def test_party_address_is_wrapped_into_priority_and_info_address_lines(
    invoice: Invoice,
):
    address = "A" * 60
    snapshot = invoice.recipient_snapshot
    snapshot.street_address = address
    snapshot.save(update_fields=["street_address"])

    xml = render_single_invoice_xml(invoice)
    sales_order = ElementTree.fromstring(xml).find("SBO_SalesOrder")
    expected_lines = [address[:35], address[35:]]

    for party_name in ("OrderParty", "BillingParty1"):
        priority_addresses = [
            sales_order.findtext(f"{party_name}/PriorityAddress{number}")
            for number in range(1, 3)
        ]
        info_addresses = [
            sales_order.findtext(f"{party_name}/InfoAddress{number}")
            for number in range(1, 3)
        ]
        assert priority_addresses == expected_lines
        assert info_addresses == expected_lines


@pytest.mark.django_db
def test_invoice_linetext_is_wrapped_into_at_most_six_sap_lines(
    invoice: Invoice, caplog
):
    description = "x" * 500
    InvoiceItem.objects.create(
        invoice=invoice,
        item_type=InvoiceItemType.LAND_USE_COMPENSATION,
        description=description,
        amount=Decimal("1250.50"),
    )

    xml = render_single_invoice_xml(invoice)
    line_item = ElementTree.fromstring(xml).find("SBO_SalesOrder/LineItem")
    linetext_elements = [
        element for element in line_item if element.tag.startswith("LineTextL")
    ]

    assert [element.tag for element in linetext_elements] == [
        f"LineTextL{number}" for number in range(1, 7)
    ]
    assert all(len(element.text or "") <= 70 for element in linetext_elements)
    assert (
        "Truncated SAP field SapLineItemContext.linetext from 500 to 420 characters; "
        "80 characters discarded."
    ) in caplog.text


@pytest.mark.django_db
def test_render_single_invoice_xml_does_not_save(invoice: Invoice):
    InvoiceItem.objects.create(
        invoice=invoice,
        item_type=InvoiceItemType.LAND_USE_COMPENSATION,
        description="Preview item",
        amount=Decimal("1250.50"),
    )

    preview_xml = render_single_invoice_xml(invoice)

    assert (
        ElementTree.fromstring(preview_xml).findtext(
            "SBO_SalesOrder/LineItem/LineTextL1"
        )
        == "Preview item"
    )
    invoice.refresh_from_db()
    assert invoice.sap_xml is None
    assert invoice.sent_at is None


@pytest.mark.django_db
def test_render_single_invoice_xml_truncates_overlong_fields_with_warning(
    invoice: Invoice, settings, caplog
):
    settings.SAP_LANDUSE_VALUES["sender_id"] = "TOO-LONG"

    xml = render_single_invoice_xml(invoice)

    assert ElementTree.fromstring(xml).findtext("SBO_SalesOrder/SenderId") == "TOO-L"
    assert "Truncated SAP field SapSalesOrderContext.sender_id" in caplog.text
    assert "3 characters discarded" in caplog.text


@pytest.mark.django_db
@patch("laske_export.landuse_export.send_invoices_xml")
def test_xml_is_immutable_after_invoice_is_sent(send_invoices_xml, invoice: Invoice):
    InvoiceItem.objects.create(
        invoice=invoice,
        item_type=InvoiceItemType.LAND_USE_COMPENSATION,
        description="Original item",
        amount=Decimal("1250.50"),
    )
    invoice.status = InvoiceStatus.WAITING_TO_BE_SENT
    invoice.due_date = timezone.localdate()
    invoice.save()
    call_command("send_landuse_invoices")
    invoice.refresh_from_db()
    original_xml = invoice.sap_xml

    invoice.due_date = date(2026, 12, 31)
    invoice.save()
    InvoiceItem.objects.create(
        invoice=invoice,
        item_type=InvoiceItemType.INTEREST,
        description="Late item",
        amount=Decimal("1.00"),
    )
    call_command("send_landuse_invoices")
    send_invoices_xml.assert_called_once()

    invoice.refresh_from_db()
    assert invoice.sap_xml == original_xml


@pytest.mark.django_db
def test_manual_invoice_identifier_is_rejected_on_creation(invoice: Invoice):
    with pytest.raises(ValidationError, match="generated automatically"):
        Invoice.objects.create(
            agreement=invoice.agreement,
            recipient_party=invoice.recipient_party,
            installment_sequence_number=1,
            installment_count_total=1,
            invoice_identifier=1_000_000_020,
        )


@pytest.mark.django_db
def test_invoice_identifier_cannot_be_changed(invoice: Invoice):
    original_identifier = invoice.invoice_identifier
    invoice.invoice_identifier += 1

    with pytest.raises(ValidationError, match="cannot be changed"):
        invoice.save()

    invoice.refresh_from_db()
    assert invoice.invoice_identifier == original_identifier


@pytest.mark.django_db
def test_render_multiple_invoices(invoice: Invoice):
    root = ElementTree.fromstring(render_invoices_xml([invoice, invoice]))

    assert root.tag == "SBO_SalesOrderContainer"
    assert len(root.findall("SBO_SalesOrder")) == 2


@pytest.mark.django_db
@pytest.mark.parametrize("has_eligible_invoice", [False, True])
@patch("laske_export.landuse_export.send_invoices_xml")
def test_send_landuse_invoices_logs_progress(
    send_invoices_xml, invoice, has_eligible_invoice, caplog
):
    caplog.set_level(logging.INFO, logger="laske_export.landuse_export")
    invoice.due_date = timezone.localdate()
    invoice.status = (
        InvoiceStatus.WAITING_TO_BE_SENT
        if has_eligible_invoice
        else InvoiceStatus.DRAFT
    )
    invoice.save()

    call_command("send_landuse_invoices")

    assert "Finding unsent land-use invoices with due dates on or before" in caplog.text
    assert f"Found {int(has_eligible_invoice)} land-use invoices to send" in caplog.text
    if has_eligible_invoice:
        assert "Sending 1 land-use invoices to SAP" in caplog.text
        assert "Sent 1 land-use invoices to SAP." in caplog.text
        send_invoices_xml.assert_called_once()
    else:
        assert "No land-use invoices to send." in caplog.text
        send_invoices_xml.assert_not_called()

    export_log = LanduseInvoiceExportLog.objects.get()
    assert export_log.succeeded is True
    assert export_log.ended_at >= export_log.started_at
    assert export_log.error == ""
    assert export_log.invoice_ids == ([invoice.pk] if has_eligible_invoice else [])
    if not has_eligible_invoice:
        assert export_log.exported_filename == ""
        assert export_log.exported_xml == ""


@pytest.mark.django_db
@patch(
    "laske_export.landuse.invoice_context._sales_order_context",
    wraps=invoice_context._sales_order_context,
)
@patch("laske_export.landuse_export.send_invoices_xml")
def test_send_landuse_invoices_batches_due_invoices(
    send_invoices_xml, sales_order_context, invoice, monkeypatch
):
    monkeypatch.setattr(timezone, "localdate", lambda: date(2026, 1, 31))
    today = timezone.localdate()
    invoice.due_date = today + relativedelta(months=1)
    invoice.status = InvoiceStatus.WAITING_TO_BE_SENT
    invoice.save()
    overdue_to_be_sent = Invoice.objects.create(
        agreement=invoice.agreement,
        recipient_party=invoice.recipient_party,
        installment_sequence_number=2,
        installment_count_total=2,
        due_date=today - relativedelta(days=1),
        invoice_type=InvoiceType.LAND_USE_COMPENSATION,
        status=InvoiceStatus.WAITING_TO_BE_SENT,
    )

    call_command("send_landuse_invoices")

    send_invoices_xml.assert_called_once()
    batch_id, xml = send_invoices_xml.call_args.args
    export_log = LanduseInvoiceExportLog.objects.get()
    assert batch_id == export_log.pk

    orders = ElementTree.fromstring(xml).findall("SBO_SalesOrder")
    assert [order.findtext("Reference") for order in orders] == [
        str(invoice.invoice_identifier),
        str(overdue_to_be_sent.invoice_identifier),
    ]
    assert export_log.invoice_ids == [invoice.pk, overdue_to_be_sent.pk]
    assert LanduseInvoiceExportLog.objects.filter(
        invoice_ids__contains=[overdue_to_be_sent.pk]
    ).exists()
    assert export_log.succeeded is True
    assert export_log.exported_filename == (
        f"MTIL_IN_ID990_9999_LANDUSE_{export_log.pk:08}.xml"
    )
    assert export_log.exported_xml == xml
    assert export_log.ended_at >= export_log.started_at

    for sent_invoice in (invoice, overdue_to_be_sent):
        sent_invoice.refresh_from_db()
        assert sent_invoice.sent_at is not None
        assert sent_invoice.status == InvoiceStatus.OPEN
        assert (
            len(ElementTree.fromstring(sent_invoice.sap_xml).findall("SBO_SalesOrder"))
            == 1
        )

        fragment = sent_invoice.sap_xml.split("<SBO_SalesOrderContainer>\n", 1)[
            1
        ].rsplit("\n</SBO_SalesOrderContainer>", 1)[0]
        assert fragment in xml

    call_command("send_landuse_invoices")
    send_invoices_xml.assert_called_once()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "excluded", ["future", "no_due_date", "sent", "draft", "open", "paid", "credited"]
)
@patch("laske_export.landuse_export.send_invoices_xml")
def test_send_landuse_invoices_excludes_ineligible_invoices(
    send_invoices_xml, invoice, excluded, monkeypatch
):
    monkeypatch.setattr(timezone, "localdate", lambda: date(2026, 1, 31))
    invoice.due_date = timezone.localdate()
    invoice.status = InvoiceStatus.WAITING_TO_BE_SENT
    if excluded == "future":
        invoice.due_date += relativedelta(months=1, days=1)
    elif excluded == "no_due_date":
        invoice.due_date = None
    elif excluded == "sent":
        invoice.sent_at = timezone.now()
    else:
        invoice.status = excluded
    invoice.save()

    call_command("send_landuse_invoices")

    send_invoices_xml.assert_not_called()
    invoice.refresh_from_db()
    assert invoice.sap_xml is None


@pytest.mark.django_db
@patch(
    "laske_export.landuse_export.send_invoices_xml",
    side_effect=OSError("Upload failed"),
)
def test_send_landuse_invoices_keeps_invoices_unsent_on_failure(
    send_invoices_xml, invoice, monkeypatch, caplog
):
    import logging

    from laske_export import landuse_export

    caplog.set_level(logging.INFO, logger="laske_export.landuse_export")

    def raise_about_missing_remote_file(export_id: int) -> None:
        raise FileNotFoundError("missing file")

    monkeypatch.setattr(
        landuse_export,
        "delete_invoices_xml_from_remote",
        raise_about_missing_remote_file,
    )
    invoice.due_date = timezone.localdate()
    invoice.status = InvoiceStatus.WAITING_TO_BE_SENT
    invoice.save()

    with pytest.raises(OSError, match="Upload failed"):
        call_command("send_landuse_invoices")

    invoice.refresh_from_db()
    assert invoice.sent_at is None
    assert invoice.sap_xml is None
    assert invoice.status == InvoiceStatus.WAITING_TO_BE_SENT

    export_log = LanduseInvoiceExportLog.objects.get()
    assert export_log.succeeded is False
    assert export_log.error == "Upload failed"
    assert export_log.invoice_ids == [invoice.pk]
    assert export_log.exported_filename.endswith(f"LANDUSE_{export_log.pk:08}.xml")
    assert export_log.exported_xml == send_invoices_xml.call_args.args[1]
    assert export_log.ended_at >= export_log.started_at
    assert "Likely the file was not uploaded at all" in caplog.text


@pytest.mark.django_db
@patch("laske_export.landuse_export.send_invoices_xml")
@patch("laske_export.landuse_export.delete_invoices_xml_from_remote")
def test_uploaded_batch_is_removed_when_database_update_fails(
    delete_invoices_xml_from_remote, send_invoices_xml, invoice, monkeypatch
):
    invoice.due_date = timezone.localdate()
    invoice.status = InvoiceStatus.WAITING_TO_BE_SENT
    invoice.save()

    def fail_bulk_update(*args, **kwargs):
        raise RuntimeError("DB update failed")

    monkeypatch.setattr(
        Invoice.objects,
        "bulk_update",
        fail_bulk_update,
    )
    with pytest.raises(RuntimeError, match="DB update failed"):
        call_command("send_landuse_invoices")

    export_log = LanduseInvoiceExportLog.objects.get()
    invoice.refresh_from_db()
    assert invoice.sent_at is None
    send_invoices_xml.assert_called_once()
    delete_invoices_xml_from_remote.assert_called_once_with(export_log.pk)


@pytest.mark.django_db
@patch(
    "laske_export.landuse_export.render_single_invoice_xml",
    side_effect=ValueError("Invalid invoice XML"),
)
@patch("laske_export.landuse_export.send_invoices_xml")
def test_send_landuse_invoices_logs_rendering_failure(
    send_invoices_xml, render_xml, invoice
):
    invoice.due_date = timezone.localdate()
    invoice.status = InvoiceStatus.WAITING_TO_BE_SENT
    invoice.save()

    with pytest.raises(ValueError, match="Invalid invoice XML"):
        call_command("send_landuse_invoices")

    export_log = LanduseInvoiceExportLog.objects.get()
    assert export_log.succeeded is False
    assert export_log.error == "Invalid invoice XML"
    assert export_log.exported_xml == ""
    assert export_log.invoice_ids == [invoice.pk]
    assert export_log.ended_at >= export_log.started_at
    send_invoices_xml.assert_not_called()
    invoice.refresh_from_db()
    assert invoice.sent_at is None
    assert invoice.status == InvoiceStatus.WAITING_TO_BE_SENT
