import datetime
from decimal import Decimal

from dateutil.relativedelta import relativedelta
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Q

from leasing.enums import InvoiceState
from leasing.models import Invoice, Lease
from leasing.models.invoice import InvoiceRow, InvoiceSet


class Command(BaseCommand):
    help = "A Bogus Invoice creator"

    def add_arguments(self, parser):
        parser.add_argument(
            "override", nargs="?", type=bool
        )  # force run even if it's not the 1st of the month

    def handle(self, *args, **options):  # noqa: C901 TODO
        override = options.get("override", False)
        today = datetime.date.today()
        today = today.replace(day=1)

        if not override and today.day != 1:
            raise CommandError(
                "Invoices should only be generated on the first day of the month"
            )

        start_of_next_month = today.replace(day=1) + relativedelta(months=1)
        end_of_next_month = start_of_next_month + relativedelta(day=31)

        self.stdout.write(
            "Finding leases with due dates between {} and {}\n".format(
                start_of_next_month, end_of_next_month
            )
        )

        leases = Lease.objects.filter(is_invoicing_enabled=True).filter(
            Q(Q(end_date=None) | Q(end_date__gte=today.replace(day=1)))
            & Q(  # ensure whole month is included when forced
                Q(start_date=None) | Q(start_date__lte=end_of_next_month)
            )
        )
        self.stdout.write(
            "Found {} leases, starting to create invoices".format(leases.count())
        )

        invoice_count = 0

        for lease in leases:
            period_rents = lease.determine_payable_rents_and_periods(
                start_of_next_month, end_of_next_month
            )

            if not period_rents:
                continue

            self.stdout.write("Lease #{} {}:".format(lease.id, lease.identifier))
            for period_invoice_data in lease.calculate_invoices(period_rents):
                invoiceset = None
                if len(period_invoice_data) > 1:
                    billing_period_start_date = period_invoice_data[0].get(
                        "billing_period_start_date"
                    )
                    billing_period_end_date = period_invoice_data[0].get(
                        "billing_period_end_date"
                    )

                    try:
                        invoiceset = InvoiceSet.objects.get(
                            lease=lease,
                            billing_period_start_date=billing_period_start_date,
                            billing_period_end_date=billing_period_end_date,
                        )
                        self.stdout.write("  Invoiceset already exists.")
                    except InvoiceSet.DoesNotExist:
                        invoiceset = InvoiceSet.objects.create(
                            lease=lease,
                            billing_period_start_date=billing_period_start_date,
                            billing_period_end_date=billing_period_end_date,
                        )

                for invoice_data in period_invoice_data:
                    invoice_data.pop("explanations")
                    invoice_data.pop("calculation_result")
                    invoice_row_data = invoice_data.pop("rows")

                    invoice_data["generated"] = True
                    invoice_data["invoiceset"] = invoiceset

                    try:
                        invoice = Invoice.objects.get(
                            **{k: v for k, v in invoice_data.items() if k != "notes"}
                        )
                        self.stdout.write(
                            "Lease #{} {}: Invoice already exists. Invoice id {}. Number {}".format(
                                lease.id, lease.identifier, invoice.id, invoice.number
                            )
                        )
                    except Invoice.DoesNotExist:
                        with transaction.atomic():
                            invoice_data["invoicing_date"] = today
                            invoice_data["outstanding_amount"] = invoice_data[
                                "billed_amount"
                            ]
                            # ensure 0€ total invoices get marked as PAID
                            if invoice_data["outstanding_amount"] == Decimal(0):
                                invoice_data["state"] = InvoiceState.PAID

                            invoice = Invoice.objects.create(**invoice_data)

                            for invoice_row_datum in invoice_row_data:
                                invoice_row_datum["invoice"] = invoice
                                InvoiceRow.objects.create(**invoice_row_datum)

                        self.stdout.write(
                            "  Invoice created. Invoice id {}. Number {}".format(
                                invoice.id, invoice.number
                            )
                        )
                        invoice_count += 1
                    except Invoice.MultipleObjectsReturned:
                        self.stdout.write(
                            "Lease #{} {}: Warning! Found multiple invoices. Not creating a new invoice.".format(
                                lease.id, lease.identifier
                            )
                        )

            self.stdout.write("")

        self.stdout.write("{} invoices created".format(invoice_count))
