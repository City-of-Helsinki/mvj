import datetime
from typing import Callable

import pytest
from django.core.management import call_command

from leasing.models.invoice import Invoice, InvoiceRow
from leasing.models.lease import Lease


@pytest.mark.django_db
def test_invoicing_not_enabled(
    lease_factory: Callable[..., Lease], caplog: pytest.LogCaptureFixture
):
    """Invoicing not enabled -> no invoices"""
    lease = lease_factory(
        start_date=datetime.date(2025, 1, 1),
        end_date=datetime.date(2025, 12, 31),
        invoicing_enabled_at=None,
    )
    for month in range(1, 13):
        call_command("create_invoices_for_single_lease", lease.pk, 2025, month)

        assert (
            f"Lease not found with ID {lease.id}, or it's not active, or invoicing is not enabled."
            in caplog.text
        )
        assert Invoice.objects.count() == 0
        assert InvoiceRow.objects.count() == 0


@pytest.mark.parametrize(
    "month", [1, 2, 3, 10, 11, 12]
)  # Lease's inactive months from the fixture
@pytest.mark.django_db
def test_no_active_leases(
    invoicing_test_data_for_create_invoices: dict[str, Lease],
    month: int,
    caplog: pytest.LogCaptureFixture,
):
    """No active leases during the target period --> no invoices"""

    # Make sure the test data is as expected
    lease = invoicing_test_data_for_create_invoices["lease"]
    assert lease.start_date == datetime.date(2025, 4, 1)
    assert lease.end_date == datetime.date(2025, 9, 30)
    assert lease.invoicing_enabled_at == datetime.date(2025, 1, 1)

    call_command("create_invoices_for_single_lease", lease.id, 2025, month)

    assert "Lease not found" in caplog.text
    assert Invoice.objects.count() == 0
    assert InvoiceRow.objects.count() == 0


@pytest.mark.parametrize(
    "month", [4, 5, 6, 7, 8, 9]
)  # Lease's active months from the fixture
@pytest.mark.django_db
def test_successful_invoice_creation(
    invoicing_test_data_for_create_invoices: dict[str, Lease],
    month: int,
    caplog: pytest.LogCaptureFixture,
):
    """Happy path: an invoice is created when the inputs are valid"""

    # Make sure the test data is as expected
    lease = invoicing_test_data_for_create_invoices["lease"]
    assert lease.start_date == datetime.date(2025, 4, 1)
    assert lease.end_date == datetime.date(2025, 9, 30)
    assert lease.invoicing_enabled_at == datetime.date(2025, 1, 1)

    # Verify that there are no other leases, invoices, or invoicerows
    assert Lease.objects.count() == 1 and Lease.objects.all().first() == lease
    invoices_qs = Invoice.objects.filter(lease=lease)
    rows_qs = InvoiceRow.objects.filter(invoice__in=invoices_qs)
    assert invoices_qs.count() == 0
    assert rows_qs.count() == 0

    call_command("create_invoices_for_single_lease", lease.id, 2025, month)

    invoices_qs = Invoice.objects.filter(
        lease=lease,
        billing_period_start_date__month=month,
        billing_period_end_date__month=month,
    )
    rows_qs = InvoiceRow.objects.filter(invoice__in=invoices_qs)

    assert invoices_qs.count() == 1
    assert rows_qs.count() == 2  # fixture data has 2 tenant shares

    assert "Found the lease" in caplog.text
    assert f"Invoice created. Invoice id {invoices_qs.first().id}" in caplog.text
    assert "1 invoices created" in caplog.text
