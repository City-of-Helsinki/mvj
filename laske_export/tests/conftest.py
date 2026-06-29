import datetime
import tempfile
import xml.etree.ElementTree as et  # noqa
from decimal import Decimal
from glob import glob
from typing import Any, Callable

import pytest
from django.conf import settings
from django.core.management.base import BaseCommand
from django.test import override_settings

from laske_export.document.invoice_sales_order_adapter import (
    invoice_sales_order_adapter_factory,
)
from laske_export.exporter import LaskeExporter, create_sales_order_with_laske_values
from laske_export.management.commands import send_invoices_to_laske
from leasing.enums import ContactType, ServiceUnitId, TenantContactType
from leasing.models import District
from leasing.models.contact import Contact
from leasing.models.decision import Decision
from leasing.models.invoice import Invoice, InvoiceRow
from leasing.models.land_area import LeaseArea, LeaseAreaAddress
from leasing.models.lease import IntendedUse, Lease, LeaseType
from leasing.models.receivable_type import ReceivableType
from leasing.models.rent import RentIntendedUse
from leasing.models.service_unit import ServiceUnit
from leasing.models.tenant import Tenant, TenantContact
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
        "export": {
            "host": "localhost",
            "port": 22,
            "username": "test",
            "password": "test",
            "directory": "/",
            "key_type": "rsa",
            "key": b"AAAAB3NzaC1yc2EAAAADAQABAAABgQCwd76MQfUDhAm7mkKNjT1LEsIdd4Xcx690jGm"
            + b"p2dDQZz3z3fUZoAOdZDsVlbAOY5JkiERgs54I01Rgfjw3ns66jaZdE7CO0xGLnqM8peVm72m7"
            + b"GBCAx8LR5oMJGETrcqcIEl7z6rAKP0Xml+TdwXVhPVH+kdnxfhL/51l0u+GZ50nL0FkGBbmAq"
            + b"uY99dPzDg3SjgFKI+FkpctsjDjtCkq7JKJDALk+spKq2arZ1QZVonyMa6N/S87d8gECscSnJn"
            + b"ZxuY1JCXj6KyiVq5NuTSR03YcLh2wrTS9VaU5ttu3lSUxBMWX9weSZwCzrD9xejYqTv2YNTms"
            + b"Zb0U1nwyoiHIA8Iq3sA65UxQ/bODcVQBGvmyM3+TFoZr5pkq07i9jEWHNbZynkTHJSjI5T8fE"
            + b"dIvBw3bmnFYDs4ZudxiF5Y5ZIsbtitQef/vh15npOgC5mpy5BPxlrYFr1PGynDbry4NFPJDBA"
            + b"Q2YrPSTLkQl+Y+2hWJhbnCDLwQLm1PbYOCG/os= test@example.com",
        }
    }


@pytest.fixture(scope="function", autouse=True)
def laske_export_from_email():
    with override_settings(LASKE_EXPORT_FROM_EMAIL="john@example.com"):
        yield


@pytest.fixture(scope="function", autouse=True)
def laske_export_announce_email():
    with override_settings(
        LASKE_EXPORT_ANNOUNCE_EMAIL="john@example.com,jane@example.com"
    ):
        yield


def get_exported_file_as_tree(settings) -> et.ElementTree:
    """
    Returns a single XML element tree based on the first found XML file.

    Args:
        settings: Django configuration set in the conftest file.
                  LASKE_EXPORT_ROOT must be unique for each test that exports a
                  file, to ensure that the correct export is returned.
    """
    files = glob(settings.LASKE_EXPORT_ROOT + "/MTIL_IN_*.xml")
    assert len(files) == 1

    exported_file = files[0]
    return et.parse(exported_file)


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
def send_invoices_to_laske_command() -> BaseCommand:
    command = send_invoices_to_laske.Command()
    return command


@pytest.fixture
def send_invoices_to_laske_command_handle(
    broken_invoice,  # Fixture initialized in test file
    invoice,  # Fixture initialized in test file
    send_invoices_to_laske_command: BaseCommand,
    monkeypatch_laske_exporter_send,
    mock_sftp,
):
    command = send_invoices_to_laske_command
    command.handle(service_unit_id=ServiceUnitId.MAKE)


@pytest.fixture
def send_invoices_to_laske_command_handle_with_unexpected_error(
    broken_invoice,  # Fixture initialized in test file
    invoice,  # Fixture initialized in test file
    send_invoices_to_laske_command: BaseCommand,
    monkeypatch_laske_exporter_send_with_error,
    mock_sftp,
):
    command = send_invoices_to_laske_command
    command.handle(service_unit_id=ServiceUnitId.MAKE)


@pytest.fixture
def exporter_full_test_setup(
    django_db_setup,
    settings,
    tmp_path,  # Unique path provided by pytest: /tmp/pytest-of-vscode/pytest-<num>
    request: pytest.FixtureRequest,  # will be indirectly passed via pytest.mark.parametrize
    contact_factory: Callable[..., Contact],
    decision_factory: Callable[..., Decision],
    district_factory: Callable[..., District],
    intended_use_factory: Callable[..., IntendedUse],
    invoice_factory: Callable[..., Invoice],
    invoice_row_factory: Callable[..., InvoiceRow],
    lease_factory: Callable[..., Lease],
    lease_area_factory: Callable[..., LeaseArea],
    lease_area_address_factory: Callable[..., LeaseAreaAddress],
    lease_type_factory: Callable[..., LeaseType],
    receivable_type_factory: Callable[..., ReceivableType],
    rent_intended_use_factory: Callable[..., RentIntendedUse],
    tenant_factory: Callable[..., Tenant],
    tenant_contact_factory: Callable[..., TenantContact],
) -> dict[str, Any]:
    """Default test data fixture for exporter tests."""
    # Ensure a unique directory for each test, so that the export XML can be
    # examined in isolation.
    settings.LASKE_EXPORT_ROOT = str(tmp_path)

    service_unit_id: ServiceUnitId = request.param
    service_unit = _setup_service_unit_for_tests(
        service_unit_id, receivable_type_factory
    )

    # Set up the lease
    lessor = contact_factory(service_unit=service_unit, sap_sales_office="1234")
    district = district_factory(identifier="99", name="DistrictName")
    intended_use = intended_use_factory(
        name="IntendedUseName", service_unit=service_unit
    )
    lease_type = lease_type_factory(
        name="LeaseTypeName",
        sap_material_code="33333333",
        sap_project_number="4444444444",
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
        sap_project_number="6666666666",
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
def exporter_lacking_test_setup(
    django_db_setup,
    settings,
    tmp_path,  # Unique path provided by pytest: /tmp/pytest-of-vscode/pytest-<num>
    request: pytest.FixtureRequest,  # will be indirectly passed via pytest.mark.parametrize
    contact_factory: Callable[..., Contact],
    district_factory: Callable[..., District],
    invoice_factory: Callable[..., Invoice],
    invoice_row_factory: Callable[..., InvoiceRow],
    lease_factory: Callable[..., Lease],
    lease_type_factory: Callable[..., LeaseType],
    receivable_type_factory: Callable[..., ReceivableType],
    tenant_factory: Callable[..., Tenant],
    tenant_contact_factory: Callable[..., TenantContact],
) -> dict[str, Any]:
    """
    Testing data fixture for KAMA-related exporter tests.
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
    service_unit_id: ServiceUnitId = request.param
    service_unit = _setup_service_unit_for_tests(
        service_unit_id, receivable_type_factory
    )

    # Set up a lease with minimal details
    district = district_factory(identifier="99", name="")
    lease_type = lease_type_factory(
        name="LeaseTypeName",
        sap_material_code=None,
        sap_project_number=None,
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
        invoicing_date=datetime.date(year=2024, month=1, day=1),
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
        sap_project_number=None,
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


def _setup_service_unit_for_tests(
    service_unit_id: ServiceUnitId,
    receivable_type_factory: Callable[..., ReceivableType],
) -> ServiceUnit:
    """Set up the service unit with mandatory export-related objects."""
    service_unit = ServiceUnit.objects.get(pk=service_unit_id)

    default_receivable_type_rent = receivable_type_factory(
        name="Maanvuokraus",
        service_unit=service_unit,
        sap_material_code=None,
        sap_project_number=None,
    )
    default_receivable_type_collateral = receivable_type_factory(
        name="Rahavakuus",
        service_unit=service_unit,
        sap_material_code="11111111",
        sap_project_number="2222222222",
    )
    service_unit.default_receivable_type_rent = default_receivable_type_rent
    service_unit.default_receivable_type_collateral = default_receivable_type_collateral
    service_unit.save()
    return service_unit


@pytest.fixture
def invoice_sales_order_adapter_billing_contact_test_setup(
    request: pytest.FixtureRequest,  # will be indirectly passed via pytest.mark.parametrize
    contact_factory: Callable[..., Contact],
    district_factory: Callable[..., District],
    intended_use_factory: Callable[..., IntendedUse],
    invoice_factory: Callable[..., Invoice],
    invoice_row_factory: Callable[..., InvoiceRow],
    lease_factory: Callable[..., Lease],
    lease_type_factory: Callable[..., LeaseType],
    receivable_type_factory: Callable[..., ReceivableType],
    tenant_factory: Callable[..., Tenant],
    tenant_contact_factory: Callable[..., TenantContact],
) -> dict[str, Any]:
    """
    Default test data fixture for billing contact resolution tests.

    Creates a shared setup with:
    - service unit with required receivable types,
    - lease with required related objects,
    - tenant with tenant contact and billing contact, both starting Jan 1 2026,
    - invoice for December 2026 billing period,
    - invoice row for the tenant.
    """
    service_unit_id: ServiceUnitId = request.param
    service_unit = _setup_service_unit_for_tests(
        service_unit_id, receivable_type_factory
    )
    lease = lease_factory(
        service_unit=service_unit,
        lessor=contact_factory(service_unit=service_unit, sap_sales_office="1234"),
        district=district_factory(identifier="99", name="District name"),
        intended_use=intended_use_factory(
            name="Lease Intended Use name", service_unit=service_unit
        ),
        type=lease_type_factory(
            name="Lease Type name",
            sap_material_code="11111111",
            sap_project_number="1111111111",
        ),
    )
    invoicerow_receivable_type = receivable_type_factory(
        name="Invoice Row Receivable Type name",
        service_unit=service_unit,
        sap_material_code="11111111",
        sap_project_number="1111111111",
    )

    # Common tenant setup starting Jan 1 2026, with no end date
    tenant = tenant_factory(
        lease=lease,
        share_numerator=1,
        share_denominator=1,
        reference=None,
    )

    tenant_contacts_contact = contact_factory(first_name="Tenant", last_name="Contact")
    tenant_contact = tenant_contact_factory(
        type=TenantContactType.TENANT,
        tenant=tenant,
        contact=tenant_contacts_contact,
        start_date=datetime.date(2026, 1, 1),
    )

    billing_contacts_contact = contact_factory(
        first_name="Original",
        last_name="Billing Contact",
        sap_customer_number="1111111111",
    )
    billing_contact = tenant_contact_factory(
        type=TenantContactType.BILLING,
        tenant=tenant,
        contact=billing_contacts_contact,
        start_date=datetime.date(2026, 1, 1),
    )

    # Common invoice setup for December 2026 billing period
    billing_period_start_date = datetime.date(year=2026, month=12, day=1)
    billing_period_end_date = datetime.date(year=2026, month=12, day=31)

    invoice = invoice_factory(
        lease=lease,
        total_amount=Decimal("111.11"),
        billed_amount=Decimal("111.11"),
        outstanding_amount=Decimal("111.11"),
        recipient=billing_contacts_contact,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
    )
    invoice_row_factory(
        invoice=invoice,
        tenant=tenant,
        receivable_type=invoicerow_receivable_type,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
        amount=Decimal("111.11"),
    )

    return {
        "service_unit": service_unit,
        "lease": lease,
        "invoicerow_receivable_type": invoicerow_receivable_type,
        "tenant": tenant,
        "tenant_contact": tenant_contact,
        "tenant_contacts_contact": tenant_contacts_contact,
        "billing_contact": billing_contact,
        "billing_contacts_contact": billing_contacts_contact,
        "invoice": invoice,
        "billing_period_start_date": billing_period_start_date,
        "billing_period_end_date": billing_period_end_date,
    }
