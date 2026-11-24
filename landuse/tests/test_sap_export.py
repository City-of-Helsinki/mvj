from unittest.mock import MagicMock, patch

import pytest

from laske_export.landuse_export import LanduseSapExportDisabledError, send_invoices_xml


@patch("laske_export.landuse_export.SFTPManager")
def test_send_invoices_xml_uploads_in_memory_xml(sftp_manager, settings):
    settings.FLAG_LANDUSE_SAP_EXPORT_ENABLED = True
    settings.SAP_LANDUSE_VALUES = {
        "sender_id": "1111",
        "sales_org": "2222",
    }
    settings.LASKE_SERVERS["landuse_export"]["directory"] = "/sap/export"
    sftp = MagicMock()
    sftp_manager.return_value.__enter__.return_value = sftp

    send_invoices_xml(42, "<Invoice>ä</Invoice>")

    sftp_manager.assert_called_once_with(profile="landuse_export")
    uploaded_file, remote_path = sftp.putfo.call_args.args
    assert uploaded_file.read() == "<Invoice>ä</Invoice>".encode("utf-8")
    expected_path = "/sap/export/MTIL_IN_1111_2222_LANDUSE_00000042.xml"
    temporary_path = f"{expected_path}.part"
    assert remote_path == temporary_path
    sftp.rename.assert_called_once_with(temporary_path, expected_path)
    sftp.remove.assert_not_called()


@pytest.mark.parametrize("failure_method", ["putfo", "rename"])
@patch("laske_export.landuse_export.SFTPManager")
def test_send_invoices_xml_cleans_up_temporary_file_on_failure(
    sftp_manager, settings, failure_method
):
    settings.FLAG_LANDUSE_SAP_EXPORT_ENABLED = True
    settings.SAP_LANDUSE_VALUES = {"sender_id": "1111", "sales_org": "2222"}
    settings.LASKE_SERVERS["landuse_export"]["directory"] = "/sap/export"
    sftp = MagicMock()
    sftp_manager.return_value.__enter__.return_value = sftp
    failure = OSError(f"{failure_method} failed")
    getattr(sftp, failure_method).side_effect = failure

    with pytest.raises(OSError, match=f"{failure_method} failed") as raised:
        send_invoices_xml(42, "<Invoice />")

    expected_path = "/sap/export/MTIL_IN_1111_2222_LANDUSE_00000042.xml"
    temporary_path = f"{expected_path}.part"
    assert raised.value is failure
    assert sftp.remove.call_args_list == [
        ((temporary_path,),),
        ((expected_path,),),
    ]


@patch("laske_export.landuse_export.SFTPManager")
def test_send_invoices_xml_does_not_connect_when_disabled(sftp_manager, settings):
    settings.FLAG_LANDUSE_SAP_EXPORT_ENABLED = False

    with pytest.raises(
        LanduseSapExportDisabledError, match="Land-use SAP export is disabled"
    ):
        send_invoices_xml(42, "<Invoice />")

    sftp_manager.assert_not_called()
