from datetime import date, datetime
from datetime import timezone as dt_timezone
from unittest.mock import patch

import pytest

from leasing.models import Invoice, Lease
from leasing.models.vat import Vat
from leasing.report.invoice.invoice_details_and_forecast import (
    InvoiceDetailsAndForecastReport,
)


@pytest.mark.django_db
def test_invoice_details_report_includes_invoice_and_lease_data(
    invoice_factory,
    service_unit_factory,
    lease_factory,
    contact_factory,
):
    service_unit = service_unit_factory()
    lease: Lease = lease_factory(service_unit=service_unit, is_subject_to_vat=True)
    sent_to_sap_at = datetime(2026, 1, 1, tzinfo=dt_timezone.utc)
    invoice: Invoice = invoice_factory(
        lease=lease,
        service_unit=service_unit,
        recipient=contact_factory(),
        total_amount=100,
        billed_amount=100,
        notes="note",
        sent_to_sap_at=sent_to_sap_at,
        due_date=date(2026, 1, 1),
    )
    vat: Vat = Vat.objects.get_for_date(invoice.due_date)
    billed_amount_including_vat = invoice.billed_amount * (1 + vat.percent / 100)

    report = InvoiceDetailsAndForecastReport()
    data = report.get_data({"service_unit": [service_unit], "year": 2026})

    assert len(data) == 1
    row = data[0]
    assert row["invoice_id"] == invoice.id
    assert row["lease_identifier"] == lease.identifier.identifier
    assert row["notes"] == "note"
    assert row["sent_to_sap_at"].tzinfo is None
    assert row["billed_amount_including_vat"] == billed_amount_including_vat

    report.set_form({"year": 2026})
    assert report.form.is_valid()
    assert report.data_as_excel(data)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "current_date, expected_months",
    [
        (date(2025, 6, 1), [6, 7, 8, 9]),
        (date(2025, 6, 15), [7, 8, 9]),
        (date(2026, 1, 1), []),
    ],
)
def test_invoice_details_report_only_forecasts_upcoming_due_dates(
    invoicing_test_data_for_create_invoices,
    invoice_factory,
    current_date,
    expected_months,
):
    lease: Lease = invoicing_test_data_for_create_invoices["lease"]
    recipient = lease.tenants.first().tenantcontact_set.first().contact
    actual_invoice = invoice_factory(
        lease=lease,
        service_unit=lease.service_unit,
        recipient=recipient,
        due_date=date(2025, 4, 1),
        total_amount=1000,
        billed_amount=1000,
    )

    with patch(
        "django.utils.timezone.now",
        return_value=datetime(current_date.year, current_date.month, current_date.day),
    ):
        report_rows = InvoiceDetailsAndForecastReport().get_data(
            {"service_unit": [lease.service_unit], "year": 2025}
        )

    invoice_rows = [row for row in report_rows if row["invoice_id"] is not None]
    forecast_rows = [row for row in report_rows if row["invoice_id"] is None]

    for row in invoice_rows:
        assert row["invoice_id"] == actual_invoice.pk

    expected_forecast_due_dates = {date(2025, month, 1) for month in expected_months}
    assert len(forecast_rows) == len(expected_forecast_due_dates)
    for row in forecast_rows:
        assert row["due_date"] in expected_forecast_due_dates
    for due_date in expected_forecast_due_dates:
        assert any(row["due_date"] == due_date for row in forecast_rows)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "invoicing_enabled, lease_end_date, expected_row_count",
    [
        (True, None, 12),
        (False, None, 0),
        (True, date(2025, 12, 31), 0),
    ],
)
def test_invoice_details_report_forecasts_next_year(
    invoicing_test_data_for_create_invoices,
    invoicing_enabled,
    lease_end_date,
    expected_row_count,
):
    lease: Lease = invoicing_test_data_for_create_invoices["lease"]
    lease.end_date = lease_end_date
    if not invoicing_enabled:
        lease.invoicing_enabled_at = None
    lease.save()
    for rent in lease.rents.all():
        rent.end_date = None
        rent.save()
        rent.contract_rents.update(end_date=None)
    for tenant in lease.tenants.all():
        tenant.tenantcontact_set.update(end_date=None)

    with patch(
        "django.utils.timezone.now",
        return_value=datetime(2025, 11, 9),
    ):
        data = InvoiceDetailsAndForecastReport().get_data(
            {"service_unit": [lease.service_unit], "year": 2026}
        )

    assert len(data) == expected_row_count
    for row in data:
        assert row["due_date"].year == 2026
