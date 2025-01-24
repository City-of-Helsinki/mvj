import os
from unittest.mock import patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings

from filescan.models import (
    FileScanResult,
    FileScanStatus,
    _delete_infected_file,
    _scan_file_task,
    schedule_file_for_virus_scanning,
)
from plotsearch.models.plot_search import AreaSearchAttachment
from utils.models.fields import PrivateFieldFile, UnsafeFileError


@override_settings(FLAG_FILE_SCAN=False)
@pytest.fixture()
def attachment_and_scan_status(
    area_search_attachment_factory, file_scan_status_factory
):
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

    private_fieldfile: PrivateFieldFile = attachment.attachment
    return {
        "attachment": attachment,
        "scan_status": scan_status,
        "private_fieldfile": private_fieldfile,
    }


@override_settings(FLAG_FILE_SCAN=False)
@pytest.mark.django_db
def test_filescan_pending(
    django_db_setup,
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

    _delete_infected_file(
        scan_status,
    )

    attachment.refresh_from_db()
    assert not attachment.attachment
    assert (
        not attachment.attachment.name
    )  # can be empty string or None depending on test flow
    assert not os.path.isfile(absolute_path)
    assert scan_status.file_deleted_at is not None


@override_settings(FLAG_FILE_SCAN=False)
@pytest.mark.django_db
def test_is_file_scanned_and_safe(
    django_db_setup,
    attachment_and_scan_status,
):
    """Test different scan_results with _is_file_scanned_and_safe()"""
    scan_status: FileScanStatus = attachment_and_scan_status["scan_status"]
    private_fieldfile: PrivateFieldFile = attachment_and_scan_status[
        "private_fieldfile"
    ]
    with override_settings(FLAG_FILE_SCAN=True):
        assert private_fieldfile._is_file_scanned_and_safe() is False

        scan_status.scanned_at = "2025-01-01T00:00:00Z"
        scan_status.save()
        assert private_fieldfile._is_file_scanned_and_safe() is True

        scan_status.error_message = "error"
        scan_status.save()
        assert private_fieldfile._is_file_scanned_and_safe() is False

        scan_status.error_message = None
        scan_status.file_deleted_at = "2025-01-01T00:00:00Z"
        scan_status.save()
        assert private_fieldfile._is_file_scanned_and_safe() is False


@override_settings(FLAG_FILE_SCAN=False)
@pytest.mark.django_db
def test_is_file_scanned_and_safe_multiple_scan_statuses(
    django_db_setup,
    attachment_and_scan_status,
    file_scan_status_factory,
):
    """
    Test different scan_results with _is_file_scanned_and_safe()
    With multiple FileScanStatus for the same file."""
    attachment: AreaSearchAttachment = attachment_and_scan_status["attachment"]
    private_fieldfile: PrivateFieldFile = attachment_and_scan_status[
        "private_fieldfile"
    ]
    _scan_status_pending: FileScanStatus = attachment_and_scan_status[  # noqa: F841
        "scan_status"
    ]
    with override_settings(FLAG_FILE_SCAN=True):
        assert private_fieldfile._is_file_scanned_and_safe() is False

    _scan_status2_safe: FileScanStatus = file_scan_status_factory(  # noqa: F841
        content_object=attachment,
        filepath=attachment.attachment.name,
        filefield_field_name="attachment",
        scanned_at="2025-01-01T00:00:00Z",
    )

    with override_settings(FLAG_FILE_SCAN=True):
        assert private_fieldfile._is_file_scanned_and_safe() is True

    _scan_status3_unsafe: FileScanStatus = file_scan_status_factory(  # noqa: F841
        content_object=attachment,
        filepath=attachment.attachment.name,
        filefield_field_name="attachment",
        file_deleted_at="2025-01-01T00:00:00Z",
    )
    with override_settings(FLAG_FILE_SCAN=True):
        assert private_fieldfile._is_file_scanned_and_safe() is False


@pytest.mark.django_db
def test_filescan_unsafe_fieldfile_open(
    django_db_setup,
    attachment_and_scan_status,
):
    """Test PrivateFieldFile.open() with feature flag on and off, and
    FileScanStatus with safe and unsafe."""
    scan_status: FileScanStatus = attachment_and_scan_status["scan_status"]
    scan_status.file_deleted_at = "2025-01-01T00:00:00Z"
    scan_status.save()
    private_fieldfile: PrivateFieldFile = attachment_and_scan_status[
        "private_fieldfile"
    ]

    with override_settings(FLAG_FILE_SCAN=True):
        with pytest.raises(UnsafeFileError):
            private_fieldfile.open()

    with override_settings(FLAG_FILE_SCAN=False):
        try:
            private_fieldfile.open()
        except UnsafeFileError:
            pytest.fail("UnsafeFileDeletedError was raised when feature flag is off")

    scan_status.file_deleted_at = None
    scan_status.scanned_at = "2025-01-01T00:00:00Z"
    scan_status.save()
    with override_settings(FLAG_FILE_SCAN=True):
        try:
            private_fieldfile.open()
        except UnsafeFileError:
            pytest.fail("UnsafeFileDeletedError was raised when file was safe")
