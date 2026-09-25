from unittest.mock import MagicMock, patch

import pytest

from landuse.sap_export import LanduseSapExportDisabledError, send_invoice_xml


@patch("landuse.sap_export.SFTPManager")
def test_send_invoice_xml_uploads_in_memory_xml(sftp_manager, settings):
    settings.FLAG_LANDUSE_SAP_EXPORT_ENABLED = True
    settings.SAP_LANDUSE_VALUES = {
        "sender_id": "1111",
        "sales_org": "2222",
    }
    settings.LANDUSE_SAP_EXPORT_DIRECTORY = "/sap/export"
    sftp = MagicMock()
    sftp_manager.return_value.__enter__.return_value = sftp

    send_invoice_xml(42, "<Invoice>ä</Invoice>")

    sftp_manager.assert_called_once_with(profile="landuse_export")
    uploaded_file, remote_path = sftp.putfo.call_args.args
    assert uploaded_file.read() == "<Invoice>ä</Invoice>".encode("utf-8")
    assert remote_path == "/sap/export/MTIL_IN_1111_2222_LANDUSE_00000042.xml"


@patch("landuse.sap_export.SFTPManager")
def test_send_invoice_xml_does_not_connect_when_disabled(sftp_manager, settings):
    settings.FLAG_LANDUSE_SAP_EXPORT_ENABLED = False

    with pytest.raises(
        LanduseSapExportDisabledError, match="Land-use SAP export is disabled"
    ):
        send_invoice_xml(42, "<Invoice />")

    sftp_manager.assert_not_called()
