import datetime
import os
import sys
import tempfile

import paramiko
import pysftp
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
from paramiko.py3compat import decodebytes

from laske_export.document.invoice_sales_order_adapter import InvoiceSalesOrderAdapter
from laske_export.document.sales_order import SalesOrder, SalesOrderContainer
from laske_export.models import LaskeExportLog
from leasing.models import Invoice, ReceivableType


def set_constant_laske_values(sales_order):
    for key, val in settings.LASKE_VALUES.items():
        setattr(sales_order, key, val)


class Command(BaseCommand):
    help = 'Send invoices to Laske'

    def save_to_file(self, xml_string, filename):
        full_path = os.path.join(settings.LASKE_EXPORT_ROOT, filename)

        with open(full_path, 'wb') as fp:
            fp.write(xml_string)

    def send(self, filename):
        # Add destination server host key
        if settings.LASKE_SERVER_KEY_TYPE == 'ssh-ed25519':
            key = paramiko.ed25519key.Ed25519Key(data=decodebytes(settings.LASKE_SERVER_KEY))
        elif 'ecdsa' in settings.LASKE_SERVER_KEY_TYPE:
            key = paramiko.ecdsakey.ECDSAKey(data=decodebytes(settings.LASKE_SERVER_KEY))
        else:
            key = paramiko.rsakey.RSAKey(data=decodebytes(settings.LASKE_SERVER_KEY))

        hostkeys = paramiko.hostkeys.HostKeys()
        hostkeys.add(settings.LASKE_SERVER_HOST, settings.LASKE_SERVER_KEY_TYPE, key)

        cnopts = pysftp.CnOpts()
        cnopts.hostkeys = hostkeys
        # Or Disable key check:
        # cnopts.hostkeys = None

        with pysftp.Connection(settings.LASKE_SERVER_HOST, port=settings.LASKE_SERVER_PORT,
                               username=settings.LASKE_SERVER_USERNAME, password=settings.LASKE_SERVER_PASSWORD,
                               cnopts=cnopts) as sftp:
            with sftp.cd(settings.LASKE_SERVER_DIRECTORY):
                sftp.put(os.path.join(settings.LASKE_EXPORT_ROOT, filename))

    def check_export_directory(self):
        if not os.path.isdir(settings.LASKE_EXPORT_ROOT):
            self.stdout.write('Directory "{}" does not exist. Please create it.'.format(settings.LASKE_EXPORT_ROOT))
            sys.exit(-1)

        try:
            fp = tempfile.TemporaryFile(dir=settings.LASKE_EXPORT_ROOT)
            fp.close()
        except PermissionError:
            self.stdout.write('Can not create file in directory "{}".'.format(settings.LASKE_EXPORT_ROOT))
            sys.exit(-1)

    def handle(self, *args, **options):
        self.check_export_directory()

        now = timezone.now()
        today = datetime.date.today()
        one_month_in_the_future = today + relativedelta(months=1)

        # TODO: Make configurable
        receivable_type_rent = ReceivableType.objects.get(pk=1)

        laske_export_log_entry = LaskeExportLog.objects.create(started_at=now)

        invoices = Invoice.objects.filter(
            due_date__gte=today,
            due_date__lte=one_month_in_the_future,
            sent_to_sap_at__isnull=True
        ).filter(id__in=[6580, 6582])

        sales_orders = []
        log_invoices = []

        for invoice in invoices:
            sales_order = SalesOrder()
            set_constant_laske_values(sales_order)

            adapter = InvoiceSalesOrderAdapter(
                invoice=invoice,
                sales_order=sales_order,
                receivable_type_rent=receivable_type_rent
            )
            adapter.set_values()

            # TODO: check sales_order validity
            sales_orders.append(sales_order)
            log_invoices.append(invoice)

        sales_order_container = SalesOrderContainer()
        sales_order_container.sales_orders = sales_orders

        laske_export_log_entry.invoices.set(log_invoices)

        export_filename = 'MTIL_IN_{}_{:08}.xml'.format(settings.LASKE_VALUES['sender_id'], laske_export_log_entry.id)

        xml_string = sales_order_container.to_xml_string()

        self.save_to_file(xml_string, export_filename)
        self.send(export_filename)

        # TODO: Log errors
        laske_export_log_entry.ended_at = timezone.now()
        laske_export_log_entry.is_finished = True
        laske_export_log_entry.save()
