import datetime
import logging
import sys
from decimal import Decimal

from dateutil.relativedelta import relativedelta
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Q

from leasing.enums import InvoiceState
from leasing.models import Invoice, Lease
from leasing.models.invoice import InvoiceRow, InvoiceSet
from leasing.models.types import InvoiceDatum

logger = logging.getLogger(__name__)
stdout_handler = logging.StreamHandler(stream=sys.stdout)
logger.addHandler(stdout_handler)
logger.setLevel(logging.INFO)


class Command(BaseCommand):
    help = "Creates invoices for all leases with due dates during the next month."

    def add_arguments(self, parser):
        parser.add_argument(
            "override", nargs="?", type=bool
        )  # force run even if it's not the 1st of the month

    def handle(self, *args, **options):
        override = options.get("override", False)
        today = get_today()

        if not override and today.day != 1:
            raise CommandError(
                "Invoices should only be generated on the first day of the month"
            )

        start_of_next_month = _get_start_of_next_month(today)
        end_of_next_month = _get_end_of_next_month(today)
        logger.info(
            f"Finding leases with possible due dates between {start_of_next_month} and {end_of_next_month}\n"
        )
        leases = Lease.objects.filter(invoicing_enabled_at__isnull=False).filter(
            q_lease_is_active_in_period(
                start_date=today.replace(
                    day=1
                ),  # ensure whole month is included when forced
                end_date=end_of_next_month,
            )
        )
        logger.info(f"Found {leases.count()} leases, starting to create invoices")

        invoices_created_count = 0

        for lease in leases:
            logger.info(f"Lease #{lease.id} {lease.identifier}:")
            invoices_created_count += create_invoices_for_lease(
                lease, start_of_next_month, end_of_next_month, today
            )
            logger.info("")

        logger.info(f"{invoices_created_count} invoices created")


def get_today() -> datetime.date:
    """Decoupled function to make testing easier."""
    return datetime.date.today()


def _get_start_of_next_month(today: datetime.date) -> datetime.date:
    return today.replace(day=1) + relativedelta(months=1)


def _get_end_of_next_month(today: datetime.date) -> datetime.date:
    start_of_next_month = _get_start_of_next_month(today)
    return start_of_next_month + relativedelta(
        day=31
    )  # relativedelta day addition does not roll over to next month


def q_lease_is_active_in_period(
    start_date: datetime.date, end_date: datetime.date
) -> Q:
    return Q(Q(end_date=None) | Q(end_date__gte=start_date)) & Q(
        Q(start_date=None) | Q(start_date__lte=end_date)
    )


def create_invoices_for_lease(
    lease: Lease,
    invoicing_start_date: datetime.date,
    invoicing_end_date: datetime.date,
    invoicing_date: datetime.date,
) -> int:
    """Returns: number of created invoices"""
    # Note: `dry_run=False` makes saves to e.g. RentAdjustment(s)
    period_rents = lease.determine_payable_rents_and_periods(
        invoicing_start_date, invoicing_end_date, dry_run=False
    )
    if not period_rents:
        logger.info(
            f"Lease #{lease.id} {lease.identifier}: No period rents to invoice."
        )
        return 0

    invoices_created_count = 0

    for period_invoice_data in lease.calculate_invoices(period_rents):
        invoiceset = None

        if len(period_invoice_data) > 1:
            invoiceset = _get_or_create_invoiceset(lease, period_invoice_data)

        for invoice_datum in period_invoice_data:
            created = _create_invoice(lease, invoice_datum, invoiceset, invoicing_date)
            if created:
                invoices_created_count += 1

    return invoices_created_count


def _get_or_create_invoiceset(
    lease: Lease, period_invoice_data: list[InvoiceDatum]
) -> InvoiceSet:
    billing_period_start_date = period_invoice_data[0].get("billing_period_start_date")
    billing_period_end_date = period_invoice_data[0].get("billing_period_end_date")

    try:
        invoiceset = InvoiceSet.objects.get(
            lease=lease,
            billing_period_start_date=billing_period_start_date,
            billing_period_end_date=billing_period_end_date,
        )
        logger.info("  Invoiceset already exists.")
    except InvoiceSet.DoesNotExist:
        invoiceset = InvoiceSet.objects.create(
            lease=lease,
            billing_period_start_date=billing_period_start_date,
            billing_period_end_date=billing_period_end_date,
        )

    return invoiceset


def _create_invoice(
    lease: Lease,
    invoice_datum: InvoiceDatum,
    invoiceset: InvoiceSet | None,
    invoicing_date: datetime.date,
) -> bool:
    """Returns: True if invoice was created, False otherwise"""
    invoice_datum.pop("explanations")
    invoice_datum.pop("calculation_result")
    invoice_row_data = invoice_datum.pop("rows")

    invoice_datum["generated"] = True
    invoice_datum["invoiceset"] = invoiceset

    try:
        invoice = Invoice.objects.get(
            **{k: v for k, v in invoice_datum.items() if k != "notes"}
        )
        logger.info(
            (
                f"Lease #{lease.id} {lease.identifier}: Invoice already exists. "
                f"Invoice id {invoice.id}. Number {invoice.number}"
            )
        )
        return False

    except Invoice.DoesNotExist:
        with transaction.atomic():
            invoice_datum["invoicing_date"] = invoicing_date
            invoice_datum["outstanding_amount"] = invoice_datum["billed_amount"]
            # ensure 0€ total invoices get marked as PAID
            if invoice_datum["outstanding_amount"] == Decimal(0):
                invoice_datum["state"] = InvoiceState.PAID

            invoice = Invoice.objects.create(**invoice_datum)

            for invoice_row_datum in invoice_row_data:
                invoice_row_datum["invoice"] = invoice
                InvoiceRow.objects.create(**invoice_row_datum)

        logger.info(
            f"  Invoice created. Invoice id {invoice.id}. Number {invoice.number}"
        )
        return True

    except Invoice.MultipleObjectsReturned:
        logger.warning(
            (
                f"Lease #{lease.id} {lease.identifier}: Warning! Found multiple invoices with same values. "
                "Not creating a new invoice."
            )
        )
        return False
