import datetime
from typing import Callable
from unittest.mock import patch

import pytest
from django.core.management import CommandError, call_command

from leasing.enums import (
    DueDatesType,
    PeriodType,
    RentCycle,
    RentType,
    TenantContactType,
)
from leasing.models.invoice import Invoice, InvoiceRow
from leasing.models.lease import Lease


@pytest.mark.django_db
def test_command_fails_not_first_of_month():
    """Should fail if today is not the first day of month, and override is not set"""
    with patch("leasing.management.commands.create_invoices.get_today") as mock_today:
        for day in range(2, 32):
            mock_today.return_value = datetime.date(2025, 1, day)

            with pytest.raises(CommandError):
                call_command("create_invoices")

            assert Invoice.objects.count() == 0
            assert InvoiceRow.objects.count() == 0


@pytest.mark.django_db
def test_no_leases_exist(caplog: pytest.LogCaptureFixture):
    """No leases --> no invoices"""
    assert Lease.objects.count() == 0

    call_command("create_invoices", "override")

    assert "Found 0 leases" in caplog.text
    assert "0 invoices created" in caplog.text
    assert Invoice.objects.count() == 0
    assert InvoiceRow.objects.count() == 0


@pytest.mark.django_db
def test_invoicing_not_enabled(
    lease_factory: Callable[..., Lease], caplog: pytest.LogCaptureFixture
):
    """If invoicing isn't enabled for the lease, it won't generate invoices even
    if it was active during the target period."""
    lease_factory(
        start_date=datetime.date(2025, 1, 1),
        end_date=datetime.date(2025, 12, 31),
        invoicing_enabled_at=None,
    )
    for month in range(1, 13):
        with patch(
            "leasing.management.commands.create_invoices.get_today"
        ) as mock_today:
            mock_today.return_value = datetime.date(2025, month, 1)

            call_command("create_invoices")

            assert "Found 0 leases" in caplog.text
            assert "0 invoices created" in caplog.text
            assert Invoice.objects.count() == 0
            assert InvoiceRow.objects.count() == 0


@pytest.mark.django_db
def test_lease_activity_periods(
    invoicing_test_data_for_create_invoices: dict[str, Lease],
    caplog: pytest.LogCaptureFixture,
):
    """Invoices are only generated for lease's active months."""

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

    # Because the command targets the month after current one, invoices won't
    # be generated in January's or February's runs.
    for month_of_run in [1, 2]:
        with patch(
            "leasing.management.commands.create_invoices.get_today"
        ) as mock_today:
            mock_today.return_value = datetime.date(2025, month_of_run, 1)
            caplog.clear()

            call_command("create_invoices")

            assert "Found 0 leases" in caplog.text
            assert "0 invoices created" in caplog.text
            assert Invoice.objects.count() == 0
            assert InvoiceRow.objects.count() == 0

    # The lease will generate invoices between March and August runs
    # (invoices from April to September)
    for month_of_run in [3, 4, 5, 6, 7, 8]:
        with patch(
            "leasing.management.commands.create_invoices.get_today"
        ) as mock_today:
            mock_today.return_value = datetime.date(2025, month_of_run, 1)
            caplog.clear()

            call_command("create_invoices")

            assert "Found 1 leases" in caplog.text

            month_of_invoice = month_of_run + 1
            invoices_qs = Invoice.objects.filter(
                lease=lease,
                billing_period_start_date__month=month_of_invoice,
                billing_period_end_date__month=month_of_invoice,
            )
            rows_qs = InvoiceRow.objects.filter(invoice__in=invoices_qs)

            assert invoices_qs.count() == 1
            assert rows_qs.count() == 2  # fixture data has 2 tenant shares
            assert (
                f"Invoice created. Invoice id {invoices_qs.first().id}" in caplog.text
            )

    # SPECIAL CASE: the ongoing month is included when collecting leases, but
    # shouldn't generate invoices for this ongoing month.
    # Apparently this is some corner use-case if the command is run out-of-cycle.
    # Would be good to verify if this extended start date filter is still needed.
    month_of_run = 9
    with patch("leasing.management.commands.create_invoices.get_today") as mock_today:
        mock_today.return_value = datetime.date(2025, month_of_run, 1)
        caplog.clear()

        call_command("create_invoices")

        assert "Found 1 leases" in caplog.text

        # Check September invoices generated in September
        # 0, because they were already generated in August's run
        invoices_qs = Invoice.objects.filter(
            lease=lease,
            billing_period_start_date__month=month_of_run,
            billing_period_end_date__month=month_of_run,
            invoicing_date=mock_today.return_value,  # only invoices generated in September
        )
        rows_qs = InvoiceRow.objects.filter(invoice__in=invoices_qs)

        assert invoices_qs.count() == 0
        assert rows_qs.count() == 0
        assert "0 invoices created" in caplog.text

        # Check October invoices (0, because lease not active)
        month_of_invoice = month_of_run + 1
        invoices_qs = Invoice.objects.filter(
            lease=lease,
            billing_period_start_date__month=month_of_invoice,
            billing_period_end_date__month=month_of_invoice,
        )
        rows_qs = InvoiceRow.objects.filter(invoice__in=invoices_qs)

        assert invoices_qs.count() == 0
        assert rows_qs.count() == 0
        assert "0 invoices created" in caplog.text

    # The lease ended in September. From October onwards the widened pre-filter
    # may still include it as a candidate (until the window's start passes the
    # lease end date)
    for month_of_run in [10, 11, 12]:
        with patch(
            "leasing.management.commands.create_invoices.get_today"
        ) as mock_today:
            mock_today.return_value = datetime.date(2025, month_of_run, 1)
            caplog.clear()

            call_command("create_invoices")

            invoices_qs = Invoice.objects.filter(
                lease=lease, billing_period_start_date__month=month_of_run
            )
            rows_qs = InvoiceRow.objects.filter(invoice__in=invoices_qs)

            assert invoices_qs.count() == 0
            assert rows_qs.count() == 0
            assert "0 invoices created" in caplog.text


@pytest.mark.django_db
def test_annual_due_date_after_lease_end(
    lease_factory: Callable[..., Lease],
    rent_factory,
    contract_rent_factory,
    rent_intended_use_factory,
    rent_due_date_factory,
    contact_factory,
    tenant_factory,
    tenant_contact_factory,
    tenant_rent_share_factory,
    caplog: pytest.LogCaptureFixture,
):
    """A lease active Jan-Mar with a single annual due date in June must generate
    an invoice when the command runs on May 1st (targeting June)."""
    lease = lease_factory(
        start_date=datetime.date(2025, 1, 1),
        end_date=datetime.date(2025, 2, 28),
        invoicing_enabled_at=datetime.date(2025, 1, 1),
    )
    rent = rent_factory(
        lease=lease,
        type=RentType.FIXED,
        cycle=RentCycle.JANUARY_TO_DECEMBER,
        due_dates_type=DueDatesType.CUSTOM,
        start_date=lease.start_date,
        end_date=lease.end_date,
    )
    # Single annual due date on June 30
    rent_due_date_factory(rent=rent, day=30, month=6)
    rent_intended_use = rent_intended_use_factory()
    contract_rent_factory(
        rent=rent,
        amount=1000,
        period=PeriodType.PER_MONTH,
        base_amount=1000,
        base_amount_period=PeriodType.PER_MONTH,
        intended_use=rent_intended_use,
        start_date=lease.start_date,
        end_date=lease.end_date,
    )
    tenant = tenant_factory(lease=lease, share_numerator=1, share_denominator=1)
    contact = contact_factory()
    tenant_contact_factory(
        contact=contact,
        tenant=tenant,
        start_date=lease.start_date,
        end_date=lease.end_date,
        type=TenantContactType.TENANT,
    )
    tenant_rent_share_factory(
        tenant=tenant,
        intended_use=rent_intended_use,
        share_numerator=1,
        share_denominator=1,
    )

    # Runs that don't target June must not create the invoice
    for month_of_run in [1, 2, 3, 6, 7]:
        with patch(
            "leasing.management.commands.create_invoices.get_today"
        ) as mock_today:
            mock_today.return_value = datetime.date(2025, month_of_run, 1)
            caplog.clear()

            call_command("create_invoices")

            assert Invoice.objects.filter(lease=lease).count() == 0
            assert "0 invoices created" in caplog.text

    # The run on May 1st targets June, where the single annual due date falls.
    with patch("leasing.management.commands.create_invoices.get_today") as mock_today:
        mock_today.return_value = datetime.date(2025, 5, 1)
        caplog.clear()

        call_command("create_invoices")

        invoices_qs = Invoice.objects.filter(lease=lease)
        assert invoices_qs.count() == 1

        assert "Found 1 leases" in caplog.text
        assert "1 invoices created" in caplog.text

        # Billing period should be clipped to the lease's active months
        invoice = invoices_qs.first()
        assert invoice.billing_period_start_date == datetime.date(2025, 1, 1)
        assert invoice.billing_period_end_date == datetime.date(2025, 2, 28)
