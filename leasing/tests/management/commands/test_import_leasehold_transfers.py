import io
import zipfile
from unittest.mock import Mock, call, patch

from leasing.management.commands.import_leasehold_transfers import Command


def test_import_discovers_archive_links_from_directory_listing(settings, tmp_path):
    settings.NLS_IMPORT_ROOT = str(tmp_path)
    settings.NLS_HELSINKI_FOLDER_URL = "https://nls.example/"
    settings.NLS_HELSINKI_USERNAME = "test-user"
    settings.NLS_HELSINKI_PASSWORD = "test-password"
    directory_listing = b"""
        <html><body><table>
            <tr><td><a href="../">Parent Directory</a></td></tr>
            <tr><td><a href="vuokraoikeudet_muuttuneet_20261119.zip">First archive</a></td></tr>
            <tr><td>
                <a href="https://nls.example/ktjkiraineistoluovutus/vuokraoikeudet_muuttuneet_20261120.zip">
                    Second archive
                </a>
            </td></tr>
            <tr><td><a href="kiinteistot_20261120.zip">Other archive</a></td></tr>
            <tr><td><a href="other.zip">vuokraoikeudet_muuttuneet</a></td></tr>
            <tr><td><a>No href</a></td></tr>
            <tr><td><a href="">Empty href</a></td></tr>
            <tr><td><span href="vuokraoikeudet_muuttuneet_not_a_link.zip">Not an anchor</span></td></tr>
        </table></body></html>
    """
    archive_buffer = io.BytesIO()
    with zipfile.ZipFile(archive_buffer, "w") as archive:
        archive.writestr("vuokraoikeustiedot.xml", b"<root />")
    archive_bytes = archive_buffer.getvalue()
    output = io.StringIO()
    command = Command(stdout=output)

    with (
        patch.object(
            command,
            "_auth_get",
            side_effect=[
                Mock(status_code=200, content=directory_listing),
                Mock(content=archive_bytes),
                Mock(content=archive_bytes),
            ],
        ) as auth_get,
        patch(
            "leasing.management.commands.import_leasehold_transfers.LeaseholdTransferImportLog"
        ) as import_log,
    ):
        import_log.objects.filter.return_value.exists.return_value = False
        import_log.objects.get_or_create.return_value = (Mock(), True)

        command.handle()

    target_folder = "https://nls.example/ktjkiraineistoluovutus/"
    expected_file_names = [
        "vuokraoikeudet_muuttuneet_20261119.zip",
        "vuokraoikeudet_muuttuneet_20261120.zip",
    ]
    assert auth_get.call_args_list == [call(target_folder)] + [
        call(target_folder + file_name) for file_name in expected_file_names
    ]
    assert import_log.objects.get_or_create.call_args_list == [
        call(file_name=file_name) for file_name in expected_file_names
    ]
    assert sorted(path.name for path in tmp_path.iterdir()) == expected_file_names
    for file_name in expected_file_names:
        assert (tmp_path / file_name).read_bytes() == archive_bytes
    assert "Imported data from 2 archive(s)" in output.getvalue()
