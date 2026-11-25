import logging
from datetime import date
from decimal import Decimal
from unittest.mock import Mock
from xml.etree import ElementTree

import pytest
from django.utils import timezone

from landuse.models.agreement import LandUseAgreement
from landuse.models.invoice import Invoice, InvoiceStatus, InvoiceType
from landuse.models.party import AgreementParty, BillingDetails
from laske_export import landuse_export
from laske_export.models import LanduseInvoiceExportLog


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
        due_date=date(2026, 2, 28),
        invoice_type=InvoiceType.LAND_USE_COMPENSATION,
        status=InvoiceStatus.WAITING_TO_BE_SENT,
        billed_amount=Decimal("1250.50"),
    )


@pytest.fixture
def export_log(db) -> LanduseInvoiceExportLog:
    return LanduseInvoiceExportLog.objects.create()


def _create_invoice(invoice: Invoice, **overrides) -> Invoice:
    values = {
        "agreement": invoice.agreement,
        "recipient_party": invoice.recipient_party,
        "installment_sequence_number": 2,
        "installment_count_total": 2,
        "due_date": invoice.due_date,
        "invoice_type": InvoiceType.LAND_USE_COMPENSATION,
        "status": InvoiceStatus.WAITING_TO_BE_SENT,
    }
    values.update(overrides)
    return Invoice.objects.create(**values)


@pytest.mark.django_db
def test_exports_only_eligible_invoices_and_marks_them_sent(
    invoice, export_log, monkeypatch
):
    monkeypatch.setattr(timezone, "localdate", lambda: date(2026, 1, 31))
    after_deadline = _create_invoice(invoice, due_date=date(2026, 3, 1))
    already_sent = _create_invoice(invoice, sent_at=timezone.now())
    draft = _create_invoice(invoice, status=InvoiceStatus.DRAFT)
    other_type = _create_invoice(invoice, invoice_type=InvoiceType.PENALTY)
    send = Mock()
    monkeypatch.setattr(landuse_export, "send_invoices_xml", send)

    landuse_export.export_landuse_compensation_invoices(export_log)

    send.assert_called_once_with(export_log.pk, export_log.exported_xml)
    assert export_log.invoice_ids == [invoice.pk]
    assert export_log.exported_filename == (
        f"MTIL_IN_ID990_9999_LANDUSE_{export_log.pk:08}.xml"
    )
    assert (
        len(ElementTree.fromstring(export_log.exported_xml).findall("SBO_SalesOrder"))
        == 1
    )

    invoice.refresh_from_db()
    assert invoice.status == InvoiceStatus.OPEN
    assert invoice.sent_at is not None
    assert invoice.sap_xml
    for excluded in (after_deadline, already_sent, draft, other_type):
        excluded.refresh_from_db()
        assert excluded.sap_xml is None
    assert after_deadline.status == InvoiceStatus.WAITING_TO_BE_SENT
    assert already_sent.status == InvoiceStatus.WAITING_TO_BE_SENT
    assert already_sent.sent_at is not None
    assert draft.status == InvoiceStatus.DRAFT
    assert other_type.status == InvoiceStatus.WAITING_TO_BE_SENT


@pytest.mark.django_db
def test_export_returns_without_sending_when_no_invoice_is_eligible(
    invoice, export_log, monkeypatch
):
    invoice.status = InvoiceStatus.DRAFT
    invoice.save()
    send = Mock()
    delete = Mock()
    monkeypatch.setattr(landuse_export, "send_invoices_xml", send)
    monkeypatch.setattr(landuse_export, "delete_invoices_xml_from_remote", delete)

    landuse_export.export_landuse_compensation_invoices(export_log)

    send.assert_not_called()
    delete.assert_not_called()
    assert export_log.invoice_ids == []
    assert export_log.exported_filename == ""
    assert export_log.exported_xml == ""


@pytest.mark.django_db
@pytest.mark.parametrize("invalid_xml_stage", ["invoice", "batch"])
def test_invalid_xml_is_raised_without_remote_cleanup(
    invoice, export_log, monkeypatch, invalid_xml_stage
):
    if invalid_xml_stage == "invoice":
        monkeypatch.setattr(
            landuse_export, "render_single_invoice_xml", lambda *args, **kwargs: "<"
        )
    else:
        monkeypatch.setattr(
            landuse_export,
            "render_sales_order_container",
            lambda *args, **kwargs: "<",
        )
    send = Mock()
    delete = Mock()
    monkeypatch.setattr(landuse_export, "send_invoices_xml", send)
    monkeypatch.setattr(landuse_export, "delete_invoices_xml_from_remote", delete)

    with pytest.raises(ElementTree.ParseError):
        landuse_export.export_landuse_compensation_invoices(export_log)

    send.assert_not_called()
    delete.assert_not_called()


@pytest.mark.django_db
@pytest.mark.parametrize("cleanup_failure", ["none", "io", "unexpected"])
def test_export_failure_cleans_up_and_reraises(
    invoice, export_log, monkeypatch, caplog, cleanup_failure
):
    caplog.set_level(logging.INFO, logger="laske_export.landuse_export")
    send_error = RuntimeError("SAP send failed")

    def fail_send(*args):
        raise send_error

    def fail_cleanup(*args):
        if cleanup_failure == "io":
            raise FileNotFoundError("remote file is missing")
        if cleanup_failure == "unexpected":
            raise RuntimeError("cleanup failed")

    delete = Mock(side_effect=fail_cleanup)
    monkeypatch.setattr(landuse_export, "send_invoices_xml", fail_send)
    monkeypatch.setattr(landuse_export, "delete_invoices_xml_from_remote", delete)

    with pytest.raises(RuntimeError, match="SAP send failed") as raised:
        landuse_export.export_landuse_compensation_invoices(export_log)

    assert raised.value is send_error
    delete.assert_called_once_with(export_log.pk)
    invoice.refresh_from_db()
    assert invoice.status == InvoiceStatus.WAITING_TO_BE_SENT
    assert invoice.sent_at is None
    assert invoice.sap_xml is None
    if cleanup_failure == "io":
        assert "Likely the file was not uploaded at all" in caplog.text
    elif cleanup_failure == "unexpected":
        assert "Failed to remove uploaded land-use invoice export" in caplog.text
