import datetime

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.utils import timezone, translation
from django.utils.translation import ugettext_lazy as _

from laske_export.exporter import LaskeExporter
from leasing.models import Invoice


def set_constant_laske_values(sales_order):
    for key, val in settings.LASKE_VALUES.items():
        setattr(sales_order, key, val)


class Command(BaseCommand):
    help = 'Send invoices to Laske'

    def handle(self, *args, **options):
        translation.activate(settings.LANGUAGE_CODE)

        exporter = LaskeExporter()
        exporter.message_output = self.stdout

        today = datetime.date.today()
        one_month_in_the_future = today + relativedelta(months=1)

        self.stdout.write('Finding unsent invoices with due dates before {}'.format(one_month_in_the_future))
        # Creating (credit) invoices with due dates in the past seems to be quite common.
        # We can't just choose all with sent_to_sap_at__isnull=True, because that's the default value...
        invoices = Invoice.objects.filter(
            # ...so we look for "modern" invoices (created in the new MVJ)
            created_at__gt=datetime.datetime(year=2019, month=10, day=9, tzinfo=timezone.get_current_timezone()),
            due_date__lte=one_month_in_the_future,
            sent_to_sap_at__isnull=True
        ).exclude(
            # Invoices due before 1.11.2018 are not in SAP so their credit notes shouldn't be be sent there either
            credited_invoice__isnull=False,
            credited_invoice__due_date__lte=datetime.date(year=2018, month=11, day=1)
        )
        self.stdout.write('Found {} unsent invoices with due dates before {}'.format(
            invoices.count(), one_month_in_the_future))

        if not invoices:
            self.stdout.write('No invoices to send. Exiting.')
            return

        laske_export_log_entry = exporter.export_invoices(invoices)

        if settings.LASKE_EXPORT_ANNOUNCE_EMAIL:
            self.stdout.write('Sending announce email to {}'.format(settings.LASKE_EXPORT_ANNOUNCE_EMAIL))

            email_content = _('MVJ ({}) sent {} invoices to Laske on {}').format(
                settings.LASKE_VALUES['sender_id'],
                laske_export_log_entry.invoices.count(),
                laske_export_log_entry.ended_at.astimezone(
                    timezone.get_current_timezone()).strftime('%d.%m.%Y %H.%M %Z')
            )

            from_email = settings.DEFAULT_FROM_EMAIL
            if hasattr(settings, 'MVJ_EMAIL_FROM'):
                from_email = settings.MVJ_EMAIL_FROM
            if hasattr(settings, 'LASKE_EXPORT_FROM_EMAIL'):
                from_email = settings.LASKE_EXPORT_FROM_EMAIL

            send_mail(
                _('MVJ ({}) transfer').format(settings.LASKE_VALUES['sender_id']),
                email_content,
                from_email,
                settings.LASKE_EXPORT_ANNOUNCE_EMAIL,
                fail_silently=False,
            )
