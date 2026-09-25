from io import BytesIO
from pathlib import PurePosixPath

from django.conf import settings

from laske_export.sftp_manager import SFTPManager


class LanduseSapExportDisabledError(Exception):
    pass


def _export_filename(invoice_id: int) -> str:
    """
    # TODO where to get sender_id and sales_org?
    # TODO verify file name format with TALPA
    """
    # TODO not ready
    values = getattr(settings, "SAP_LANDUSE_VALUES", None)
    if values is None:
        raise ValueError("SAP_LANDUSE_VALUES is not configured in settings.")

    return "MTIL_IN_{}_{}_LANDUSE_{:08}.xml".format(
        values.get("sender_id", ""),
        values.get("sales_org", ""),
        invoice_id,
    )


def send_invoice_xml(invoice_id: int, xml: str) -> None:
    """Upload an in-memory land-use invoice XML document to SAP."""
    if not settings.FLAG_LANDUSE_SAP_EXPORT_ENABLED:
        raise LanduseSapExportDisabledError("Land-use SAP export is disabled.")

    filename = _export_filename(invoice_id)
    remote_path = str(PurePosixPath(settings.LANDUSE_SAP_EXPORT_DIRECTORY) / filename)

    with SFTPManager(profile="landuse_export") as sftp:
        sftp.putfo(BytesIO(xml.encode("utf-8")), remote_path)
