import xml.etree.ElementTree as ElementTree
from datetime import date
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.core.exceptions import ValidationError

from landuse.models.agreement import LandUseAgreement
from landuse.models.invoice import (
    INVOICE_STATUSES_BEFORE_SAP_EXPORT,
    Invoice,
    InvoiceItem,
    InvoiceItemType,
    InvoiceStatus,
    InvoiceType,
    LandUseInvoiceExportError,
)
from landuse.models.party import AgreementParty, BillingDetails


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
@patch("landuse.models.invoice.send_invoice_xml")
def test_invoice_xml_is_generated_only_when_sent(send_invoice_xml, invoice: Invoice):
    assert invoice.sap_xml is None

    invoice.save()
    assert invoice.sap_xml is None

    invoice.send_to_sap()

    root = ElementTree.fromstring(invoice.sap_xml or "")
    sales_order = root.find("SBO_SalesOrder")

    assert root.tag == "SBO_SalesOrderContainer"
    assert sales_order is not None
    assert sales_order.findtext("SenderId") == "ID990"
    assert sales_order.findtext("Reference") == str(invoice.invoice_identifier)
    assert sales_order.findtext("ContractNumber") == "M-2026-1"
    assert sales_order.findtext("OrderType") == "ZTY1"
    assert sales_order.findtext("BillingDate") == "20261031"
    assert sales_order.findtext("OrderParty/PriorityName1") == "Example & Sons"
    assert sales_order.findtext("OrderParty/SAPCustomerID") == "1000123"
    assert sales_order.findtext("BillingParty1/CustomerOVT") == "003712345678"
    assert invoice.sent_at is not None
    assert invoice.status == InvoiceStatus.OPEN
    send_invoice_xml.assert_called_once_with(invoice.pk, invoice.sap_xml)


@pytest.mark.django_db
def test_generate_sap_xml_previews_without_saving(invoice: Invoice):
    InvoiceItem.objects.create(
        invoice=invoice,
        item_type=InvoiceItemType.LAND_USE_COMPENSATION,
        description="Preview item",
        amount=Decimal("1250.50"),
    )

    preview_xml = invoice.get_sap_xml()

    assert (
        ElementTree.fromstring(preview_xml).findtext(
            "SBO_SalesOrder/LineItem/LineTextL1"
        )
        == "Preview item"
    )
    invoice.refresh_from_db()
    assert invoice.sap_xml is None
    assert invoice.sent_at is None


def test_generate_sap_xml_requires_saved_invoice():
    with pytest.raises(ValueError, match="must be saved"):
        Invoice().get_sap_xml()


@pytest.mark.django_db
@patch("landuse.models.invoice.send_invoice_xml")
def test_generate_sap_xml_returns_saved_xml(send_invoice_xml, invoice: Invoice):
    invoice.send_to_sap()
    saved_xml = invoice.sap_xml

    # Once XML is stored it should be immutable and not change.
    invoice.invoice_identifier = 1_000_000_011

    assert invoice.get_sap_xml() == saved_xml


@pytest.mark.django_db
@patch("landuse.models.invoice.send_invoice_xml")
def test_xml_is_immutable_after_invoice_is_sent(send_invoice_xml, invoice: Invoice):
    InvoiceItem.objects.create(
        invoice=invoice,
        item_type=InvoiceItemType.LAND_USE_COMPENSATION,
        description="Original item",
        amount=Decimal("1250.50"),
    )
    invoice.send_to_sap()
    original_xml = invoice.sap_xml

    invoice.due_date = date(2026, 12, 31)
    invoice.save()
    InvoiceItem.objects.create(
        invoice=invoice,
        item_type=InvoiceItemType.INTEREST,
        description="Late item",
        amount=Decimal("1.00"),
    )
    with pytest.raises(LandUseInvoiceExportError, match="already been sent to SAP"):
        invoice.send_to_sap()

    invoice.refresh_from_db()
    assert invoice.sap_xml == original_xml


@pytest.mark.django_db
@pytest.mark.parametrize(
    "status, should_raise",
    [
        (
            status,
            status not in INVOICE_STATUSES_BEFORE_SAP_EXPORT,
        )
        for status, _ in InvoiceStatus.choices
    ],
)
@patch("landuse.models.invoice.send_invoice_xml")
def test_invoice_export_is_allowed_only_for_pre_export_statuses(
    send_invoice_xml, invoice: Invoice, status, should_raise
):
    invoice.status = status
    invoice.save()

    if should_raise:
        with pytest.raises(LandUseInvoiceExportError, match="already been sent to SAP"):
            invoice.send_to_sap()
        send_invoice_xml.assert_not_called()
    else:
        invoice.send_to_sap()
        send_invoice_xml.assert_called_once_with(invoice.pk, invoice.sap_xml)
        assert invoice.sent_at is not None
        assert invoice.status == InvoiceStatus.OPEN


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
