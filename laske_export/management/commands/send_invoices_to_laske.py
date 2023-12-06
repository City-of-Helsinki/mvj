import datetime
import logging
import re

from constance import config
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone, translation
from django.utils.translation import gettext_lazy as _

from laske_export.enums import LaskeExportLogInvoiceStatus
from laske_export.exporter import LaskeExporter
from leasing.models import Invoice, ServiceUnit


class Command(BaseCommand):
    help = "Send invoices to Laske"

    def add_arguments(self, parser):
        parser.add_argument("service_unit_id", type=int)

    def handle(self, *args, **options):  # noqa
        translation.activate(settings.LANGUAGE_CODE)

        try:
            service_unit = ServiceUnit.objects.get(pk=options["service_unit_id"])
        except ServiceUnit.DoesNotExist:
            self.stdout.write(
                "Service unit with id {} not found! Exiting.".format(
                    options["service_unit_id"]
                )
            )
            return

        if (
            not service_unit.default_receivable_type_rent
            or not service_unit.default_receivable_type_collateral
        ):
            raise CommandError(
                "Service unit must have both default_receivable_type_rent and"
                " default_receivable_type_collateral set"
            )

        error_flag = False
        error_message = ""

        # noinspection PyBroadException
        try:
            exporter = LaskeExporter(service_unit=service_unit)
            exporter.message_output = self.stdout

            today = datetime.date.today()
            one_month_in_the_future = today + relativedelta(months=1)

            self.stdout.write(
                "Finding unsent invoices with due dates on or before {}".format(
                    one_month_in_the_future
                )
            )
            # Creating (credit) invoices with due dates in the past seems to be quite common.
            # We can't just choose all with sent_to_sap_at__isnull=True, because that's the default value...
            invoices = Invoice.objects.filter(
                # ...so we look for "modern" invoices (created in the new MVJ)
                created_at__gt=datetime.datetime(
                    year=2019, month=10, day=9, tzinfo=timezone.get_current_timezone()
                ),
                due_date__lte=one_month_in_the_future,
                sent_to_sap_at__isnull=True,
                service_unit=service_unit,
            ).exclude(
                # Invoices due before 1.11.2018 are not in SAP so their credit notes
                # shouldn't be sent there either
                credited_invoice__isnull=False,
                credited_invoice__due_date__lte=datetime.date(
                    year=2018, month=11, day=1
                ),
            )
            self.stdout.write(
                "Found {} unsent invoices with due dates on or before {}".format(
                    invoices.count(), one_month_in_the_future
                )
            )

            if not invoices:
                self.stdout.write("No invoices to send. Exiting.")
                return

            laske_export_log_entry = exporter.export_invoices(invoices)
        except Exception as err:
            error_flag = True
            error_message = str(err)
            self.stdout.write(
                "An error occurred in the invoice exporting. Error: {}".format(
                    error_message
                )
            )
            logging.exception(err)

        if config.LASKE_EXPORT_ANNOUNCE_EMAIL:
            email_headers = None

            if error_flag:
                self.stdout.write(
                    "Sending error email to {}".format(
                        config.LASKE_EXPORT_ANNOUNCE_EMAIL
                    )
                )
                email_headers = {"X-Priority": "1"}  # High
                email_subject = _("MVJ ({}) transfer failed!").format(
                    service_unit.laske_sender_id
                )
                email_body = _(
                    "Sending invoices to the Laske system has been crashed during the processing. "
                    "Please contact your administrator.\n"
                    "Service unit: {}\n"
                    "\nError message: {}"
                ).format(service_unit.name, error_message)
            else:
                self.stdout.write(
                    "Sending announce email to {}".format(
                        config.LASKE_EXPORT_ANNOUNCE_EMAIL
                    )
                )

                export_invoice_log_items = (
                    laske_export_log_entry.laskeexportloginvoiceitem_set
                )
                sent_count = export_invoice_log_items.filter(
                    status=LaskeExportLogInvoiceStatus.SENT
                ).count()
                failed_count = export_invoice_log_items.filter(
                    status=LaskeExportLogInvoiceStatus.FAILED
                ).count()

                email_subject = _("MVJ ({}) transfer").format(
                    service_unit.laske_sender_id
                )

                email_body = _(
                    "MVJ ({}) processed a total of {} invoices to Laske system on {}. "
                    "Of the invoices, {} succeeded and {} failed.\n"
                    "Service unit: {}"
                ).format(
                    service_unit.laske_sender_id,
                    laske_export_log_entry.invoices.count(),
                    laske_export_log_entry.ended_at.astimezone(
                        timezone.get_current_timezone()
                    ).strftime("%d.%m.%Y %H.%M %Z"),
                    sent_count,
                    failed_count,
                    service_unit.name,
                )

                if failed_count > 0:
                    email_body += "\n\n"
                    email_body += _("Failed invoice numbers:") + ""
                    for invoice in laske_export_log_entry.invoices.filter(
                        laskeexportloginvoiceitem__status=LaskeExportLogInvoiceStatus.FAILED
                    ):
                        email_body += "\n* #{} ({})".format(
                            invoice.number, invoice.lease.identifier
                        )

            from_email = settings.DEFAULT_FROM_EMAIL
            if hasattr(settings, "MVJ_EMAIL_FROM"):
                from_email = settings.MVJ_EMAIL_FROM
            if hasattr(settings, "LASKE_EXPORT_FROM_EMAIL"):
                from_email = config.LASKE_EXPORT_FROM_EMAIL

            msg = EmailMultiAlternatives(
                email_subject,
                email_body,
                from_email,
                re.split("[;,]", config.LASKE_EXPORT_ANNOUNCE_EMAIL),
                headers=email_headers,
            )
            msg.send(fail_silently=False)
