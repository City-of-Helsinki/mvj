import datetime
import logging
import sys

from dateutil.relativedelta import relativedelta
from django.core.management.base import BaseCommand

from leasing.management.commands.create_invoices import (
    create_invoices_for_lease,
    q_lease_is_active_in_period,
)
from leasing.models import Lease

logger = logging.getLogger(__name__)
stdout_handler = logging.StreamHandler(stream=sys.stdout)
logger.addHandler(stdout_handler)
logger.setLevel(logging.INFO)


class Command(BaseCommand):
    help = (
        "Creates invoices for a single lease for a given year and month.\n"
        "Example invocation for invoice 123123, March of year 2025:\n"
        "`python manage.py create_invoices_for_single_lease 123123 2025 3`"
    )

    def add_arguments(self, parser):
        parser.add_argument("lease_id", type=int, help="ID of the lease to process")
        parser.add_argument(
            "year",
            type=int,
            help="Year for the month for which to create invoices",
        )
        parser.add_argument(
            "month",
            type=int,
            choices=range(1, 13),
            help="Month for which to create invoices (1-12)",
        )

    def handle(self, *args, **options):
        lease_id: int = options.get("lease_id")  # type: ignore
        year: int = options.get("year")  # type: ignore
        month: int = options.get("month")  # type: ignore

        today = datetime.date.today()
        start_date = datetime.date(year=year, month=month, day=1)
        end_date = datetime.date(year=year, month=month, day=1) + relativedelta(
            day=31
        )  # relativedelta day addition does not roll over to next month

        logger.info(
            (
                f"Finding a lease with id {lease_id} that might have due dates "
                f"between {start_date} and {end_date}"
            )
        )
        lease = (
            Lease.objects.filter(id=lease_id, invoicing_enabled_at__isnull=False)
            .filter(q_lease_is_active_in_period(start_date, end_date))
            .first()
        )
        if not lease:
            logger.warning(
                f"Lease not found with ID {lease_id}, or it's not active, or invoicing is not enabled."
            )
            return

        logger.info("Found the lease, starting to create invoices")
        created_count = create_invoices_for_lease(lease, start_date, end_date, today)
        logger.info("{} invoices created".format(created_count))
