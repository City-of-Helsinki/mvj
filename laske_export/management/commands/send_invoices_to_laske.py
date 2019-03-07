import datetime

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.core.management.base import BaseCommand

from laske_export.exporter import LaskeExporter
from leasing.models import Invoice


def set_constant_laske_values(sales_order):
    for key, val in settings.LASKE_VALUES.items():
        setattr(sales_order, key, val)


class Command(BaseCommand):
    help = 'Send invoices to Laske'

    def handle(self, *args, **options):
        exporter = LaskeExporter()

        today = datetime.date.today()
        one_month_in_the_future = today + relativedelta(months=1)

        invoices = Invoice.objects.filter(
            due_date__gte=today,
            due_date__lte=one_month_in_the_future,
            sent_to_sap_at__isnull=True
        )

        if not invoices:
            self.stdout.write('No invoices to send. Exiting.')
            return

        exporter.export_invoices(invoices)
