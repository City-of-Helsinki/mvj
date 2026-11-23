import logging
import sys
from typing import Any

from dateutil.relativedelta import relativedelta
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from landuse.invoice_xml import (
    render_sales_order_container,
    render_single_invoice_xml,
)
from landuse.models.invoice import (
    Invoice,
    InvoiceStatus,
)
from laske_export.landuse_export import _get_export_filename, send_invoices_xml
from laske_export.models import LanduseInvoiceExportLog

logger = logging.getLogger(__name__)
stdout_handler = logging.StreamHandler(stream=sys.stdout)
logger.addHandler(stdout_handler)
logger.setLevel(logging.INFO)


class Command(BaseCommand):
    help = "Send unsent land-use invoices due within one month to SAP."

    def handle(self, *args: Any, **options: Any) -> None:
        export_log = LanduseInvoiceExportLog.objects.create()
        try:
            self._export_invoices(export_log)
        except Exception as error:
            export_log.error = str(error)
            logger.exception(f"Land-use invoice export failed: {error}")
            raise
        else:
            export_log.succeeded = True
        finally:
            export_log.ended_at = timezone.now()
            export_log.save()

    @transaction.atomic
    def _export_invoices(self, export_log: LanduseInvoiceExportLog) -> None:
        latest_due_date = timezone.localdate() + relativedelta(months=1)
        logger.info(
            f"Finding unsent land-use invoices with due dates on or before {latest_due_date}"
        )
        invoices = list(
            Invoice.objects.select_for_update()
            .filter(
                due_date__lte=latest_due_date,
                sent_at__isnull=True,
                status=InvoiceStatus.WAITING_TO_BE_SENT,
            )
            .order_by("pk")
        )
        logger.info(f"Found {len(invoices)} land-use invoices to send")
        if not invoices:
            logger.info("No land-use invoices to send.")
            return

        export_log.invoice_ids = [invoice.pk for invoice in invoices]
        export_log.exported_filename = _get_export_filename(export_log.pk)
        sales_orders = [
            render_single_invoice_xml(invoice, include_container=False)
            for invoice in invoices
        ]
        xml = render_sales_order_container(sales_orders)
        export_log.exported_xml = xml
        invoice_xmls = [render_sales_order_container([order]) for order in sales_orders]
        logger.info(f"Sending {len(invoices)} land-use invoices to SAP")
        send_invoices_xml(export_log.pk, xml)

        sent_at = timezone.now()
        for invoice, invoice_xml in zip(invoices, invoice_xmls):
            invoice.sap_xml = invoice_xml
            invoice.sent_at = sent_at
            invoice.status = InvoiceStatus.OPEN
            invoice.modified_at = sent_at
        Invoice.objects.bulk_update(
            invoices, ("sap_xml", "sent_at", "status", "modified_at")
        )
        logger.info(f"Sent {len(invoices)} land-use invoices to SAP.")
