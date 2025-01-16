import os
from unittest.mock import patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings

from filescan.models import (
    FileScanResult,
    FileScanStatus,
    _delete_file,
    _scan_file_task,
    schedule_file_for_virus_scanning,
)
from plotsearch.models.plot_search import AreaSearchAttachment

# FIXME the attachments I generate in tests still use <app root>/private_files/ directory
# FIXME tmpdir is not deleted after test run
# @pytest.fixture(scope="module")
# def module_temp_dir():
#     """
#     Creates a temporary directory for the tests, sets that directory as the
#     target directory for files to be scanned, and automatically deletes the
#     directory and all the files within after all in the module tests are done.
#     """
#     # FIXME tests still save the files to private_files
#     with tempfile.TemporaryDirectory() as tmpdir:
#         with override_settings(PRIVATE_FILES_LOCATION=tmpdir):
#             yield tmpdir


@override_settings(FLAG_FILE_SCAN=False)
@pytest.mark.django_db
def test_filescan_pending(
    django_db_setup,
    # module_temp_dir,
    file_scan_status_factory,
    area_search_attachment_factory,
):
    """FileScans that have not been scanned are pending"""
    filename = "test_attachment.pdf"
    file = SimpleUploadedFile(
        name=filename, content=b"test", content_type="application/pdf"
    )
    attachment: AreaSearchAttachment = area_search_attachment_factory(attachment=file)
    scan: FileScanStatus = file_scan_status_factory(
        content_object=attachment, filepath=attachment.attachment.name
    )
    assert scan.scan_result() == FileScanResult.PENDING


@override_settings(FLAG_FILE_SCAN=False)
@pytest.mark.django_db
def test_filescan_safe(
    django_db_setup,
    # module_temp_dir,
    area_search_attachment_factory,
):
    """Files scanned as "safe" are handled correctly: not deleted."""
    filename = "test_attachment.pdf"
    file = SimpleUploadedFile(
        name=filename, content=b"test", content_type="application/pdf"
    )
    attachment: AreaSearchAttachment = area_search_attachment_factory(attachment=file)
    with patch("requests.post") as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "success": True,
            "data": {
                "result": [
                    {
                        "name": filename,
                        "is_infected": False,
                        "viruses": [],
                    }
                ]
            },
        }
        with patch("filescan.models.async_task") as mock_async_task:
            scan = schedule_file_for_virus_scanning(attachment, "attachment")
            if not scan:
                pytest.fail()

            args, _ = mock_async_task.call_args
            scan_task, scan_pk = args

            assert scan_task == _scan_file_task
            assert scan_pk == scan.pk

            _scan_file_task(scan_pk)

            scan.refresh_from_db()
            assert scan.scan_result() == FileScanResult.SAFE
            # FieldFile (attachment.attachment) is truthy if it contains a reference to a file
            assert attachment.attachment
            assert os.path.isfile(attachment.attachment.path)
            assert scan.file_deleted_at is None


@override_settings(FLAG_FILE_SCAN=False)
@pytest.mark.django_db
def test_filescan_unsafe(
    django_db_setup,
    # module_temp_dir,
    area_search_attachment_factory,
):
    """Files scanned as "unsafe" are handled correctly: deleted."""
    filename = "test_attachment.pdf"
    file = SimpleUploadedFile(
        name=filename, content=b"test", content_type="application/pdf"
    )
    attachment: AreaSearchAttachment = area_search_attachment_factory(attachment=file)
    with patch("requests.post") as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "success": True,
            "data": {
                "result": [
                    {
                        "name": filename,
                        "is_infected": True,
                        "viruses": ["Some_virus.exe"],
                    }
                ]
            },
        }
        with patch("filescan.models.async_task") as mock_async_task:
            scan = schedule_file_for_virus_scanning(attachment, "attachment")
            if not scan:
                pytest.fail()

            args, _ = mock_async_task.call_args
            scan_task, scan_pk = args
            absolute_path = attachment.attachment.path

            assert scan_task == _scan_file_task
            assert scan_pk == scan.pk

            _scan_file_task(scan_pk)

            scan.refresh_from_db()
            attachment.refresh_from_db()
            assert scan.scan_result() == FileScanResult.UNSAFE
            assert not attachment.attachment
            assert (
                not attachment.attachment.name
            )  # can be empty string or None depending on test flow
            assert not os.path.isfile(absolute_path)
            assert scan.file_deleted_at is not None


@override_settings(FLAG_FILE_SCAN=False)
@pytest.mark.django_db
def test_file_deletion(
    django_db_setup,
    # module_temp_dir,
    file_scan_status_factory,
    area_search_attachment_factory,
):
    """File deletion deletes the actual file, and sets FileField value to NULL"""
    filename = "test_attachment.pdf"
    file = SimpleUploadedFile(
        name=filename, content=b"test", content_type="application/pdf"
    )
    attachment: AreaSearchAttachment = area_search_attachment_factory(attachment=file)
    scan_status: FileScanStatus = file_scan_status_factory(
        content_object=attachment,
        filepath=attachment.attachment.name,
        filefield_field_name="attachment",
    )

    absolute_path = attachment.attachment.path

    # FieldFile (attachment.attachment) is truthy if it contains a reference to a file
    assert attachment.attachment
    # FieldFile.name contains a value if FieldFile contains a reference to a file
    assert attachment.attachment.name is not None
    assert os.path.isfile(absolute_path)
    assert scan_status.file_deleted_at is None

    _delete_file(
        scan_status,
    )

    attachment.refresh_from_db()
    assert not attachment.attachment
    assert (
        not attachment.attachment.name
    )  # can be empty string or None depending on test flow
    assert not os.path.isfile(absolute_path)
    assert scan_status.file_deleted_at is not None
