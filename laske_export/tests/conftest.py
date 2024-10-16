import datetime
import os
import tempfile
from decimal import Decimal
from typing import Any, Type

import pytest
from django.conf import settings

from conftest import ReceivableTypeFactory
from laske_export.document.invoice_sales_order_adapter import (
    invoice_sales_order_adapter_factory,
)
from laske_export.exporter import create_sales_order_with_laske_values
from leasing.enums import ContactType, ServiceUnitId, TenantContactType
from leasing.models import ServiceUnit
from leasing.tests.conftest import *  # noqa


def pytest_configure():
    """
    Pytest hook to set common configurations for all test files that use this conftest.

    Temporary directory will be shared by tests in a single file.
    If you require a unique directory for your test, use the `tmp_path` fixture:
    https://docs.pytest.org/en/stable/how-to/tmp_path.html
    """
    laske_export_root = tempfile.mkdtemp(prefix="laske-export-")
    settings.LANGUAGE_CODE = "en"
    settings.LASKE_EXPORT_ROOT = laske_export_root
    settings.LASKE_SERVERS = {
        "export": {"host": "localhost", "username": "test", "password": "test"}
    }


def pytest_runtest_setup(item):
    if item.get_closest_marker("ftp") and os.environ.get(
        "TEST_FTP_ACTIVE", False
    ) not in [1, "1", True, "True"]:
        pytest.skip("test requires TEST_FTP_ACTIVE to be true")


ftp_settings = {
    "payments": {
        "host": os.getenv("FTP_HOST", "ftp"),
        "port": 21,
        "username": "test",
        "password": "test",
        "directory": "/payments",
    }
}


@pytest.fixture
def setup_ftp(monkeypatch, use_ftp):
    monkeypatch.setattr(settings, "LASKE_SERVERS", ftp_settings)
    ftp = use_ftp
    ftp.mkd("/payments")
    ftp.cwd("/payments")
    ftp.mkd("arch/")
    yield
    # Cleanup all the folders / files from ftp after test
    ftp.cwd("/payments")
    arch_files = ftp.nlst("arch/")
    payment_files = ftp.nlst()
    for obj in arch_files:
        ftp.delete(obj)
    for payment_file in payment_files:
        try:
            ftp.delete(payment_file)
        except Exception:
            ftp.rmd(payment_file)
            continue
    ftp.cwd("/")
    ftp.rmd("payments/")
    ftp.quit()


@pytest.fixture
def use_ftp():
    from ftplib import FTP

    ftp = FTP(
        host=ftp_settings["payments"]["host"],
        user=ftp_settings["payments"]["username"],
        passwd=ftp_settings["payments"]["password"],
        timeout=100,
    )
    return ftp


@pytest.fixture(scope="function", autouse=True)
def laske_export_from_email(override_config):
    with override_config(LASKE_EXPORT_FROM_EMAIL="john@example.com"):
        yield


@pytest.fixture(scope="function", autouse=True)
def laske_export_announce_email(override_config):
    with override_config(
        LASKE_EXPORT_ANNOUNCE_EMAIL="john@example.com,jane@example.com"
    ):
        yield


@pytest.fixture
def akv_default_test_setup(
    django_db_setup,
    settings,
    tmp_path,  # Unique path provided by pytest: /tmp/pytest-of-vscode/pytest-<num>
    contact_factory,
    decision_factory,
    district_factory,
    intended_use_factory,
    invoice_factory,
    invoice_row_factory,
    lease_factory,
    lease_area_factory,
    lease_area_address_factory,
    lease_type_factory,
    receivable_type_factory,
    rent_intended_use_factory,
    tenant_factory,
    tenant_contact_factory,
) -> dict[str, Any]:
    """Default test data fixture for AKV-related exporter tests."""
    # Ensure a unique directory for each test, so that the export XML can be
    # examined in isolation.
    settings.LASKE_EXPORT_ROOT = str(tmp_path)

    service_unit = _setup_akv_service_unit_for_tests(receivable_type_factory)

    # Set up the lease
    lessor = contact_factory(service_unit=service_unit, sap_sales_office="1234")
    district = district_factory(identifier="99", name="DistrictName")
    intended_use = intended_use_factory(
        name="IntendedUseName", service_unit=service_unit
    )
    lease_type = lease_type_factory(
        name="LeaseTypeName",
        sap_material_code="33333333",
        sap_order_item_number="4444444444",
    )
    lease = lease_factory(
        service_unit=service_unit,
        lessor=lessor,
        district=district,
        intended_use=intended_use,
        type=lease_type,
    )
    decision = decision_factory(
        lease=lease,
        reference_number="HEL 2024-123456",
        decision_date=datetime.date(year=2024, month=1, day=1),
        section="111",
    )

    # Set up the lease areas
    # Lease can have multiple LeaseAreas, which can have multiple LeaseAreaAddresses
    lease_area1 = lease_area_factory(
        lease=lease,
        area=100,
        archived_decision=decision,
    )
    lease_area1_address1 = lease_area_address_factory(
        lease_area=lease_area1,
        address="LeaseArea1Address 1",
        postal_code="00100",
        city="LeaseAreaCity",
        is_primary=False,  # Non-primary address should be ignored if primary address exists
    )
    lease_area1_address2 = lease_area_address_factory(
        lease_area=lease_area1,
        address="LeaseArea1Address 2",
        postal_code="00100",
        city="LeaseAreaCity",
        is_primary=True,  # This address should be selected: first area, primary address
    )
    lease_area2 = lease_area_factory(lease=lease, area=200)
    lease_area2_address1 = lease_area_address_factory(
        lease_area=lease_area2,
        address="LeaseArea2Address 1",
        postal_code="00100",
        city="LeaseAreaCity",
        is_primary=False,
    )
    lease_area2_address2 = lease_area_address_factory(
        lease_area=lease_area2,
        address="LeaseArea2Address 2",
        postal_code="00100",
        city="LeaseAreaCity",
        is_primary=True,
    )

    # Set up the invoice
    tenant = tenant_factory(
        lease=lease,
        share_numerator=1,
        share_denominator=1,
        reference="Tenant1Reference",
    )
    contact = contact_factory(
        type=ContactType.PERSON,
        first_name="Contact1FirstName",
        last_name="Contact1LastName",
    )
    tenant_contact_factory(
        type=TenantContactType.TENANT,
        tenant=tenant,
        contact=contact,
        start_date=datetime.date(year=2024, month=1, day=1),
    )
    invoice1_billing_period_start_date = datetime.date(year=2024, month=1, day=1)
    invoice1_billing_period_end_date = datetime.date(year=2024, month=12, day=31)

    invoice1 = invoice_factory(
        lease=lease,
        total_amount=Decimal("123.45"),
        billed_amount=Decimal("123.45"),
        outstanding_amount=Decimal("123.45"),
        recipient=contact_factory(
            first_name="RecipientFirstName",
            last_name="RecipientLastName",
            type=ContactType.PERSON,
        ),
        billing_period_start_date=invoice1_billing_period_start_date,
        billing_period_end_date=invoice1_billing_period_end_date,
    )
    invoicerow1_receivable_type = receivable_type_factory(
        name="InvoiceRow1ReceivableType",
        service_unit=service_unit,
        sap_material_code="55555555",
        sap_order_item_number="6666666666",
    )
    invoicerow1_intended_use = rent_intended_use_factory(name="Muu")
    invoicerow1 = invoice_row_factory(
        invoice=invoice1,
        tenant=tenant,
        receivable_type=invoicerow1_receivable_type,
        billing_period_start_date=invoice1_billing_period_start_date,
        billing_period_end_date=invoice1_billing_period_end_date,
        amount=Decimal("123.45"),
        intended_use=invoicerow1_intended_use,
    )

    # Set up the sales order and invoice adapter
    sales_order = create_sales_order_with_laske_values(invoice1.service_unit)
    adapter = invoice_sales_order_adapter_factory(
        invoice=invoice1,
        sales_order=sales_order,
        service_unit=service_unit,
    )
    adapter.set_values()

    return {
        "service_unit": service_unit,
        "lessor": lessor,
        "district": district,
        "intended_use": intended_use,
        "lease": lease,
        "decision": decision,
        "lease_area1": lease_area1,
        "lease_area1_address1": lease_area1_address1,
        "lease_area1_address2": lease_area1_address2,
        "lease_area2": lease_area2,
        "lease_area2_address1": lease_area2_address1,
        "lease_area2_address2": lease_area2_address2,
        "tenant": tenant,
        "contact": contact,
        "invoice1": invoice1,
        "invoice1_billing_period_start_date": invoice1_billing_period_start_date,
        "invoice1_billing_period_end_date": invoice1_billing_period_end_date,
        "invoicerow1": invoicerow1,
        "invoicerow1_receivable_type": invoicerow1_receivable_type,
        "invoicerow1_intended_use": invoicerow1_intended_use,
        "sales_order": sales_order,
        "adapter": adapter,
    }


@pytest.fixture
def akv_lacking_test_setup(
    django_db_setup,
    settings,
    tmp_path,
    contact_factory,
    district_factory,
    invoice_factory,
    invoice_row_factory,
    lease_factory,
    lease_type_factory,
    receivable_type_factory,
    tenant_factory,
    tenant_contact_factory,
) -> dict[str, Any]:
    """
    Testing data fixture for AKV-related exporter tests.
    Is purposefully lacking some details that should be part of all invoice
    exports, such as:
    - lease areas
    - lease area address
    - decision
    - intended use
    - rent intended use

    The parameters to factory functions set here should be the minimum
    requirements needed to pass model instance creation constraints.
    """
    settings.LASKE_EXPORT_ROOT = str(tmp_path)

    # Set up the service unit
    service_unit = _setup_akv_service_unit_for_tests(receivable_type_factory)

    # Set up a lease with minimal details
    district = district_factory(identifier="99", name="")
    lease_type = lease_type_factory(
        name="LeaseTypeName",
        sap_material_code=None,
        sap_order_item_number=None,
    )
    lease = lease_factory(
        service_unit=service_unit,
        lessor=None,
        district=district,
        intended_use=None,
        type=lease_type,
    )
    # Purposefully omit creating lease areas, address, decision...

    # Set up the invoice
    tenant = tenant_factory(
        lease=lease,
        share_numerator=1,
        share_denominator=1,
        reference=None,
    )
    contact = contact_factory(
        type=ContactType.PERSON,
        first_name=None,
        last_name=None,
    )
    tenant_contact_factory(
        type=TenantContactType.TENANT,
        tenant=tenant,
        contact=contact,
        start_date=datetime.date(year=2024, month=1, day=1),
    )
    invoice1 = invoice_factory(
        lease=lease,
        total_amount=Decimal("123.45"),
        billed_amount=Decimal("123.45"),
        outstanding_amount=Decimal("123.45"),
        recipient=contact_factory(
            first_name=None,
            last_name=None,
            type=ContactType.PERSON,
        ),
    )
    invoicerow1_receivable_type = receivable_type_factory(
        name="InvoiceRow1ReceivableType",
        service_unit=service_unit,
        sap_material_code=None,
        sap_order_item_number=None,
    )
    invoicerow1 = invoice_row_factory(
        invoice=invoice1,
        tenant=None,
        receivable_type=invoicerow1_receivable_type,
        billing_period_start_date=None,
        billing_period_end_date=None,
        amount=Decimal("123.45"),
        intended_use=None,
    )

    # Set up the sales order and invoice adapter
    sales_order = create_sales_order_with_laske_values(invoice1.service_unit)
    adapter = invoice_sales_order_adapter_factory(
        invoice=invoice1,
        sales_order=sales_order,
        service_unit=service_unit,
    )
    adapter.set_values()

    return {
        "service_unit": service_unit,
        "lease": lease,
        "invoice1": invoice1,
        "invoicerow1": invoicerow1,
        "sales_order": sales_order,
        "adapter": adapter,
    }


def _setup_akv_service_unit_for_tests(
    receivable_type_factory: Type[ReceivableTypeFactory],
) -> ServiceUnit:
    """Set up the AKV service unit with mandatory related objects."""
    akv_service_unit = ServiceUnit.objects.get(pk=ServiceUnitId.AKV)
    default_receivable_type_rent = receivable_type_factory(
        name="Maanvuokraus",
        service_unit=akv_service_unit,
        sap_material_code=None,
        sap_order_item_number=None,
    )
    default_receivable_type_collateral = receivable_type_factory(
        name="Rahavakuus",
        service_unit=akv_service_unit,
        sap_material_code="11111111",
        sap_order_item_number="2222222222",
    )
    akv_service_unit.default_receivable_type_rent = default_receivable_type_rent
    akv_service_unit.default_receivable_type_collateral = (
        default_receivable_type_collateral
    )
    akv_service_unit.save()
    return akv_service_unit
