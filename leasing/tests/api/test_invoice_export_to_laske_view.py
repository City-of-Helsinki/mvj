import xml.etree.ElementTree as et  # noqa
from decimal import Decimal
from glob import glob

import pytest
from django.test import override_settings
from django.urls import reverse

from laske_export.exporter import LaskeExporter
from leasing.enums import ContactType


@pytest.mark.django_db
@override_settings(LASKE_EXPORT_ANNOUNCE_EMAIL=None)
def test_export_one_invoice(
    settings,
    tmp_path,
    monkeypatch,
    admin_client,
    service_unit_factory,
    lease_factory,
    contact_factory,
    invoice_factory,
    mock_sftp,
):
    settings.LASKE_EXPORT_ROOT = str(tmp_path)
    if any(
        [
            not hasattr(settings, "LASKE_SERVERS"),
            not settings.LASKE_SERVERS.get("export", {}).get("host"),
            not settings.LASKE_SERVERS.get("export", {}).get("username"),
            not settings.LASKE_SERVERS.get("export", {}).get("password"),
            not settings.LASKE_SERVERS.get("export", {}).get("port"),
            not settings.LASKE_SERVERS.get("export", {}).get("key_type"),
            not settings.LASKE_SERVERS.get("export", {}).get("key"),
            not settings.LASKE_SERVERS.get("export", {}).get("directory"),
        ]
    ):
        settings.LASKE_SERVERS = {
            "export": {
                "host": "localhost",
                "username": "test",
                "password": "test",
                "port": 22,
                "key_type": "rsa",
                "key": b"-----BEGIN RSA PRIVATE KEY-----\nABCDF\n-----END RSA PRIVATE",
                "directory": "/",
            }
        }

    service_unit = service_unit_factory(
        invoice_number_sequence_name="test_sequence",
        first_invoice_number=123,
        laske_sender_id="TEST1",
        laske_sales_org="ORG1",
    )

    lease = lease_factory(
        type_id=1,
        municipality_id=1,
        district_id=5,
        notice_period_id=1,
        service_unit=service_unit,
    )

    contact = contact_factory(
        first_name="First name", last_name="Last name", type=ContactType.PERSON
    )

    invoice = invoice_factory(
        lease=lease,
        total_amount=Decimal("123.45"),
        billed_amount=Decimal("123.45"),
        outstanding_amount=Decimal("123.45"),
        recipient=contact,
        service_unit=service_unit,
    )

    def mocked_send(*args, **kwargs):
        pass

    monkeypatch.setattr(LaskeExporter, "send", mocked_send)

    url = reverse("v1:invoice-export-to-laske") + "?invoice={}".format(invoice.id)
    response = admin_client.post(url)

    assert response.status_code == 200, "%s %s" % (response.status_code, response.data)

    invoice.refresh_from_db()

    assert invoice.number == service_unit.first_invoice_number

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
