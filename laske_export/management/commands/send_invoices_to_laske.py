import datetime

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.utils import translation
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

        self.stdout.write('Finding unsent invoices with due dates between {} and {}'.format(
            today, one_month_in_the_future))

        invoices = Invoice.objects.filter(
            due_date__gte=today,
            due_date__lte=one_month_in_the_future,
            sent_to_sap_at__isnull=True
        )

        if not invoices:
            self.stdout.write('No invoices to send. Exiting.')
            return

        laske_export_log_entry = exporter.export_invoices(invoices)

        if settings.LASKE_EXPORT_ANNOUNCE_EMAIL:
            self.stdout.write('Sending announce email to {}'.format(settings.LASKE_EXPORT_ANNOUNCE_EMAIL))

            email_content = _('MVJ ({}) sent {} invoices to Laske on {}').format(
                settings.LASKE_VALUES['sender_id'],
                laske_export_log_entry.invoices.count(),
                laske_export_log_entry.ended_at.strftime('%d.%m.%Y %H.%M')
            )

            send_mail(
                _('MVJ ({}) transfer').format(settings.LASKE_VALUES['sender_id']),
                email_content,
                settings.MVJ_EMAIL_FROM,
                [settings.LASKE_EXPORT_ANNOUNCE_EMAIL],
                fail_silently=False,
            )
