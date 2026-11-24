import logging
from io import BytesIO
from pathlib import PurePosixPath
from xml.etree import ElementTree

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from landuse.invoice_xml import render_sales_order_container, render_single_invoice_xml
from landuse.landuse_types import SapLanduseExportValues
from landuse.models.invoice import Invoice, InvoiceStatus, InvoiceType
from laske_export.models import LanduseInvoiceExportLog
from laske_export.sftp_manager import SFTPManager

logger = logging.getLogger(__name__)


class LanduseSapExportDisabledError(Exception):
    pass


def _get_export_filename(export_id: int) -> str:
    values: SapLanduseExportValues | None = getattr(
        settings, "SAP_LANDUSE_VALUES", None
    )
    if values is None:
        raise ValueError("SAP_LANDUSE_VALUES is not configured in settings.")

    return "MTIL_IN_{}_{}_LANDUSE_{:08}.xml".format(
        values.get("sender_id", ""),
        values.get("sales_org", ""),
        export_id,
    )


def send_invoices_xml(export_id: int, xml: str) -> None:
    """Upload an in-memory land-use invoice batch XML document to SAP."""
    if not getattr(settings, "FLAG_LANDUSE_SAP_EXPORT_ENABLED", False):
        raise LanduseSapExportDisabledError("Land-use SAP export is disabled.")

    filename = _get_export_filename(export_id)
    try:
        export_directory = getattr(settings, "LASKE_SERVERS")["landuse_export"][
            "directory"
        ]
    except (ValueError, KeyError):
        raise ValueError("Landuse Export Directory is not configured in settings.")

    remote_path = str(PurePosixPath(export_directory) / filename)
    temporary_remote_path = f"{remote_path}.part"

    sftp = None
    try:
        with SFTPManager(profile="landuse_export") as sftp:
            sftp.putfo(BytesIO(xml.encode("utf-8")), temporary_remote_path)
            sftp.rename(temporary_remote_path, remote_path)
    except Exception:
        if sftp is not None:
            _remove_remote_files(sftp, temporary_remote_path, remote_path)
        raise


def _remove_remote_files(sftp, *remote_paths: str) -> None:
    for remote_path in remote_paths:
        try:
            sftp.remove(remote_path)
        except Exception:
            logger.exception(
                "Failed to remove remote land-use invoice export %s", remote_path
            )


def delete_invoices_xml_from_remote(export_id: int) -> None:
    filename = _get_export_filename(export_id)
    export_directory = settings.LASKE_SERVERS["landuse_export"]["directory"]
    remote_path = str(PurePosixPath(export_directory) / filename)
    with SFTPManager(profile="landuse_export") as sftp:
        sftp.remove(remote_path)


def export_landuse_compensation_invoices(export_log: LanduseInvoiceExportLog) -> None:
    # Only send invoices max 1 month ahead of the due date, to ensure that SAP's
    # invoicing period has been opened for the upcoming month.
    latest_due_date = timezone.localdate() + relativedelta(months=1)
    logger.info(
        f"Finding unsent land-use invoices with due dates on or before {latest_due_date}"
    )
    try:
        with transaction.atomic():
            invoices = list(
                Invoice.objects.select_for_update()
                .filter(
                    due_date__lte=latest_due_date,
                    sent_at__isnull=True,
                    status=InvoiceStatus.WAITING_TO_BE_SENT,
                    invoice_type=InvoiceType.LAND_USE_COMPENSATION,
                )
                .order_by("pk")
            )
            logger.info(f"Found {len(invoices)} land-use invoices to send")
            if not invoices:
                logger.info("No land-use invoices to send.")
                return

            export_log.invoice_ids = [invoice.pk for invoice in invoices]
            export_log.exported_filename = _get_export_filename(export_log.pk)
            sales_orders = get_sales_order_xmls(invoices)
            xml = render_sales_order_container(sales_orders)

            # Validate XML before continuing
            ElementTree.fromstring(xml.encode("utf-8"))

            export_log.exported_xml = xml
            invoice_xmls = [
                render_sales_order_container([order]) for order in sales_orders
            ]

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
    except ElementTree.ParseError:
        logger.error("Generated SAP XML is invalid.")
        raise
    except Exception:
        try:
            delete_invoices_xml_from_remote(export_log.pk)
        except IOError:
            logger.info(
                "Unable to delete land-use invoice export %s. "
                "Likely the file was not uploaded at all, nothing to clean up.",
                export_log.pk,
            )
        except Exception:
            logger.exception(
                "Failed to remove uploaded land-use invoice export %s",
                export_log.pk,
            )
        raise
    logger.info(f"Sent {len(invoices)} land-use invoices to SAP.")


def get_sales_order_xmls(invoices: list[Invoice]) -> list[str]:
    """
    Generate and validate sales order XMLs for a list of invoices.

    Raises:
        ElementTree.ParseError: If any generated sales order XML is invalid.
    """
    sales_order_xmls = []
    for invoice in invoices:
        sales_order_xml = render_single_invoice_xml(invoice, include_container=False)

        try:
            ElementTree.fromstring(sales_order_xml.encode("utf-8"))
        except ElementTree.ParseError:
            logger.error(
                "Generated sales order XML is invalid for invoice %s.", invoice.pk
            )
            raise

        sales_order_xmls.append(sales_order_xml)

    return sales_order_xmls
