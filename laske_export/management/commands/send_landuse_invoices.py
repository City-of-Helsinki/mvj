import logging
import sys
from typing import Any

from django.core.management.base import BaseCommand
from django.utils import timezone

from laske_export.landuse_export import export_landuse_compensation_invoices
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
            export_landuse_compensation_invoices(export_log)

        except Exception as error:
            export_log.error = str(error)
            logger.exception(f"Land-use invoice export failed: {error}")
            raise
        else:
            export_log.succeeded = True
        finally:
            export_log.ended_at = timezone.now()
            export_log.save()
