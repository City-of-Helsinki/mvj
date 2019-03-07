import os
import tempfile

import paramiko
import pysftp
from django.conf import settings
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from paramiko.py3compat import decodebytes

from laske_export.document.invoice_sales_order_adapter import InvoiceSalesOrderAdapter
from laske_export.document.sales_order import SalesOrder, SalesOrderContainer
from laske_export.models import LaskeExportLog
from leasing.models import Invoice, ReceivableType


def set_constant_laske_values(sales_order):
    for key, val in settings.LASKE_VALUES.items():
        setattr(sales_order, key, val)


class LaskeExporterException(Exception):
    pass


class LaskeExporter:
    def __init__(self):
        self._check_export_directory()
        self._check_settings()

    def _check_export_directory(self):
        if not os.path.isdir(settings.LASKE_EXPORT_ROOT):
            raise LaskeExporterException(
                _('Directory "{}" does not exist. Please create it.')
                .format(settings.LASKE_EXPORT_ROOT)
            )

        try:
            fp = tempfile.TemporaryFile(dir=settings.LASKE_EXPORT_ROOT)
            fp.close()
        except PermissionError:
            raise LaskeExporterException(
                _('Can not create file in directory "{}".')
                .format(settings.LASKE_EXPORT_ROOT)
            )

    def _check_settings(self):
        if (not hasattr(settings, 'LASKE_SERVERS') or
                'export' not in settings.LASKE_SERVERS or
                not settings.LASKE_SERVERS.get('export') or
                not settings.LASKE_SERVERS['export'].get('host') or
                not settings.LASKE_SERVERS['export'].get('username') or
                not settings.LASKE_SERVERS['export'].get('password')):
            raise LaskeExporterException(_('LASKE_SERVERS["export"] settings missing'))

    def save_to_file(self, xml_string, filename):
        full_path = os.path.join(settings.LASKE_EXPORT_ROOT, filename)

        with open(full_path, 'wb') as fp:
            fp.write(xml_string)

    def send(self, filename):
        # Add destination server host key
        if settings.LASKE_SERVERS['export']['key_type'] == 'ssh-ed25519':
            key = paramiko.ed25519key.Ed25519Key(data=decodebytes(settings.LASKE_SERVERS['export']['key']))
        elif 'ecdsa' in settings.LASKE_SERVERS['export']['key_type']:
            key = paramiko.ecdsakey.ECDSAKey(data=decodebytes(settings.LASKE_SERVERS['export']['key']))
        else:
            key = paramiko.rsakey.RSAKey(data=decodebytes(settings.LASKE_SERVERS['export']['key']))

        hostkeys = paramiko.hostkeys.HostKeys()
        hostkeys.add(settings.LASKE_SERVERS['export']['host'], settings.LASKE_SERVERS['export']['key_type'], key)

        cnopts = pysftp.CnOpts()
        cnopts.hostkeys = hostkeys
        # Or Disable key check:
        # cnopts.hostkeys = None

        with pysftp.Connection(settings.LASKE_SERVERS['export']['host'], port=settings.LASKE_SERVERS['export']['port'],
                               username=settings.LASKE_SERVERS['export']['username'],
                               password=settings.LASKE_SERVERS['export']['password'],
                               cnopts=cnopts) as sftp:
            with sftp.cd(settings.LASKE_SERVERS['export']['directory']):
                sftp.put(os.path.join(settings.LASKE_EXPORT_ROOT, filename))

    def export_invoices(self, invoices):
        """
        :type invoices: list of Invoice | Invoice
        :rtype: bool
        """
        if isinstance(invoices, Invoice):
            invoices = [invoices]

        # TODO: Make configurable
        receivable_type_rent = ReceivableType.objects.get(pk=1)

        now = timezone.now()
        laske_export_log_entry = LaskeExportLog.objects.create(started_at=now)

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

        Invoice.objects.filter(id__in=[o.id for o in invoices]).update(sent_to_sap_at=now)

        # TODO: Log errors
        laske_export_log_entry.ended_at = timezone.now()
        laske_export_log_entry.is_finished = True
        laske_export_log_entry.save()
