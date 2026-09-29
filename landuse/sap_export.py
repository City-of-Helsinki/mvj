from io import BytesIO
from pathlib import PurePosixPath

from django.conf import settings

from landuse.types import SapLanduseExportValues
from laske_export.sftp_manager import SFTPManager


class LanduseSapExportDisabledError(Exception):
    pass


def _get_export_filename(invoice_id: int) -> str:
    values: SapLanduseExportValues | None = getattr(
        settings, "SAP_LANDUSE_VALUES", None
    )
    if values is None:
        raise ValueError("SAP_LANDUSE_VALUES is not configured in settings.")

    return "MTIL_IN_{}_{}_LANDUSE_{:08}.xml".format(
        values.get("sender_id", ""),
        values.get("sales_org", ""),
        invoice_id,
    )


def send_invoice_xml(invoice_id: int, xml: str) -> None:
    """Upload an in-memory land-use invoice XML document to SAP."""
    if not getattr(settings, "FLAG_LANDUSE_SAP_EXPORT_ENABLED", False):
        raise LanduseSapExportDisabledError("Land-use SAP export is disabled.")

    filename = _get_export_filename(invoice_id)
    export_directory = getattr(settings, "LANDUSE_SAP_EXPORT_DIRECTORY")
    remote_path = str(PurePosixPath(export_directory) / filename)

    with SFTPManager(profile="landuse_export") as sftp:
        sftp.putfo(BytesIO(xml.encode("utf-8")), remote_path)
