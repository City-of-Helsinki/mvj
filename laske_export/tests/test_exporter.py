import datetime
import json
import xml.etree.ElementTree as et  # noqa
from decimal import Decimal
from glob import glob

import pytest
from constance.test import override_config
from django.core import mail

from laske_export.enums import LaskeExportLogInvoiceStatus
from laske_export.exporter import LaskeExporter
from laske_export.management.commands import send_invoices_to_laske
from laske_export.models import LaskeExportLog
from leasing.enums import ContactType


@pytest.fixture(scope="session")
def monkeypatch_session(request):
    """Experimental (https://github.com/pytest-dev/pytest/issues/363)."""
    from _pytest.monkeypatch import MonkeyPatch

    mpatch = MonkeyPatch()
    yield mpatch
    mpatch.undo()


@pytest.fixture
def monkeypatch_laske_exporter_send(monkeypatch_session):
    def laske_exporter_send(self, filename):
        pass

    monkeypatch_session.setattr(LaskeExporter, "send", laske_exporter_send)


laske_exporter_send_with_error__error_message = "Unexpected error!"


@pytest.fixture
def monkeypatch_laske_exporter_send_with_error(monkeypatch_session):
    def laske_exporter_send(self, filename):
        raise Exception(laske_exporter_send_with_error__error_message)

    monkeypatch_session.setattr(LaskeExporter, "send", laske_exporter_send)


@pytest.fixture
def billing_period():
    billing_period_start_date = datetime.date(year=2017, month=7, day=1)
    billing_period_end_date = datetime.date(year=2017, month=12, day=31)
    return billing_period_start_date, billing_period_end_date


@pytest.fixture
def lease(lease_factory):
    lease = lease_factory(
        type_id=1, municipality_id=1, district_id=5, notice_period_id=1
    )
    return lease


@pytest.fixture
def invoice(contact_factory, invoice_factory, lease, billing_period):
    billing_period_start_date, billing_period_end_date = billing_period

    contact = contact_factory(
        name="Company", type=ContactType.BUSINESS, business_id="1234567-8",
    )

    invoice = invoice_factory(
        lease=lease,
        total_amount=Decimal("123.45"),
        billed_amount=Decimal("123.45"),
        outstanding_amount=Decimal("123.45"),
        recipient=contact,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
    )

    return invoice


@pytest.fixture
def broken_invoice(contact_factory, invoice_factory, lease, billing_period):
    billing_period_start_date, billing_period_end_date = billing_period

    broken_contact = contact_factory(
        name="Broken Company",
        type=ContactType.BUSINESS,
        business_id="1234567-89",  # Incorrect business id
    )

    broken_invoice = invoice_factory(
        lease=lease,
        total_amount=Decimal("123.45"),
        billed_amount=Decimal("123.45"),
        outstanding_amount=Decimal("123.45"),
        recipient=broken_contact,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
    )

    return broken_invoice


@pytest.fixture
def send_invoices_to_laske_command():
    command = send_invoices_to_laske.Command()
    return command


@pytest.fixture
def send_invoices_to_laske_command_handle(
    broken_invoice,
    invoice,
    send_invoices_to_laske_command,
    monkeypatch_laske_exporter_send,
):
    command = send_invoices_to_laske_command
    command.handle(service_unit_id=1)


@pytest.fixture
def send_invoices_to_laske_command_handle_with_unexpected_error(
    broken_invoice,
    invoice,
    send_invoices_to_laske_command,
    monkeypatch_laske_exporter_send_with_error,
):
    command = send_invoices_to_laske_command
    command.handle(service_unit_id=1)


@pytest.fixture
def land_use_agreement_invoice(
    contact_factory, land_use_agreement_invoice_factory, land_use_agreement_test_data
):
    contact = contact_factory(
        name="Company", type=ContactType.BUSINESS, business_id="1234567-8",
    )

    invoice = land_use_agreement_invoice_factory(
        land_use_agreement=land_use_agreement_test_data,
        total_amount=Decimal("123.45"),
        recipient=contact,
    )

    return invoice


@pytest.mark.django_db
def test_invalid_export_invoice(
    broken_invoice, invoice, land_use_agreement_invoice, monkeypatch_laske_exporter_send
):
    exporter = LaskeExporter(service_unit=invoice.service_unit)
    exporter.export_invoices([broken_invoice, invoice])
    exporter.export_land_use_agreement_invoices([land_use_agreement_invoice])

    logs = LaskeExportLog.objects.all()
    assert logs.count() == 2

    log = logs[1]
    assert log.invoices.count() == 2

    log_items = log.laskeexportloginvoiceitem_set.all()
    assert log_items.count() == 2

    failed_invoice_logs = log_items.filter(status=LaskeExportLogInvoiceStatus.FAILED)
    assert failed_invoice_logs.count() == 1
    failed_invoice_log = failed_invoice_logs[0]
    assert failed_invoice_log.status == LaskeExportLogInvoiceStatus.FAILED
    error_json = json.loads(failed_invoice_log.information)
    assert "customer_yid" in error_json

    sent_invoice_logs = log_items.filter(status=LaskeExportLogInvoiceStatus.SENT)
    assert sent_invoice_logs.count() == 1


@pytest.mark.django_db
def test_send_invoices_to_laske_command_handle(
    broken_invoice, send_invoices_to_laske_command_handle
):
    broken_invoice.refresh_from_db()

    assert len(mail.outbox) == 1

    export_mail = mail.outbox[0]
    assert "Failed" in export_mail.body
    assert (
        "#{} ({})".format(broken_invoice.number, broken_invoice.lease.identifier)
        in export_mail.body
    )


@pytest.mark.django_db
def test_send_invoices_to_laske_command_handle_with_unexpected_error(
    send_invoices_to_laske_command_handle_with_unexpected_error,
):
    assert len(mail.outbox) == 1

    export_mail = mail.outbox[0]
    assert "X-Priority" in export_mail.extra_headers
    assert export_mail.extra_headers["X-Priority"] == "1"  # High
    assert laske_exporter_send_with_error__error_message in export_mail.body


@pytest.mark.django_db
@override_config(LASKE_EXPORT_ANNOUNCE_EMAIL=None)
@pytest.mark.parametrize("service_unit_to_use", [0, 1])
def test_send_invoices_service_unit(
    settings,
    tmp_path,
    service_unit_factory,
    lease_factory,
    contact_factory,
    invoice_factory,
    send_invoices_to_laske_command,
    monkeypatch_laske_exporter_send,
    service_unit_to_use,
):
    settings.LASKE_EXPORT_ROOT = str(tmp_path)

    service_units = [
        service_unit_factory(
            invoice_number_sequence_name="test_sequence",
            first_invoice_number=1,
            laske_sender_id="TEST1",
            laske_sales_org="ORG1",
        ),
        service_unit_factory(
            invoice_number_sequence_name="test_sequence2",
            first_invoice_number=500,
            laske_sender_id="TEST2",
            laske_sales_org="ORG2",
        ),
    ]

    leases = [
        lease_factory(
            type_id=1,
            municipality_id=1,
            district_id=5,
            notice_period_id=1,
            service_unit=service_units[0],
        ),
        lease_factory(
            type_id=1,
            municipality_id=1,
            district_id=5,
            notice_period_id=1,
            service_unit=service_units[1],
        ),
    ]

    contacts = [
        contact_factory(
            first_name="First name", last_name="Last name", type=ContactType.PERSON
        ),
        contact_factory(
            first_name="First name2", last_name="Last name2", type=ContactType.PERSON
        ),
    ]

    invoices = [
        invoice_factory(
            lease=leases[0],
            total_amount=Decimal("123.45"),
            billed_amount=Decimal("123.45"),
            outstanding_amount=Decimal("123.45"),
            recipient=contacts[0],
            service_unit=service_units[0],
        ),
        invoice_factory(
            lease=leases[1],
            total_amount=Decimal("123.45"),
            billed_amount=Decimal("123.45"),
            outstanding_amount=Decimal("123.45"),
            recipient=contacts[1],
            service_unit=service_units[1],
        ),
    ]

    service_unit = service_units[service_unit_to_use]

    command = send_invoices_to_laske_command
    command.handle(service_unit_id=service_unit.id)

    invoice = invoices[service_unit_to_use]
    invoice.refresh_from_db()

    assert invoice.number == service_unit.first_invoice_number

    other_invoice = invoices[0 if service_unit_to_use == 1 else 1]
    other_invoice.refresh_from_db()

    # Check that the invoice in the other service unit has not been handled
    assert other_invoice.number is None
    assert other_invoice.sent_to_sap_at is None

    # Find the exported xml file and check that there is only one file
    files = glob(settings.LASKE_EXPORT_ROOT + "/MTIL_IN_*.xml")
    assert len(files) == 1
    exported_file = files[0]

    # Check that the file name has the sender ID in it
    assert service_unit.laske_sender_id in exported_file

    # Check that the XML has the correct values from the service unit
    tree = et.parse(exported_file)
    assert len(tree.findall("./SBO_SalesOrder")) == 1
    assert tree.find("./SBO_SalesOrder/SalesOrg").text == service_unit.laske_sales_org
    assert tree.find("./SBO_SalesOrder/Reference").text == str(invoice.number)
