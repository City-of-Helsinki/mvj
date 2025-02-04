import os
from unittest.mock import patch

import pytest
from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.utils import timezone

from filescan.models import (
    FileScanResult,
    FileScanStatus,
    TestGenericAttachmentModel,
    TestGenericSafeDeleteAttachmentModel,
    _delete_infected_file,
    _scan_file_task,
    schedule_file_for_virus_scanning,
)
from utils.models.fields import (
    FileScanError,
    FileScanPendingError,
    FileUnsafeError,
    PrivateFieldFile,
)


@override_settings(FLAG_FILE_SCAN=False)
@pytest.fixture()
def generic_test_data(file_scan_status_factory):
    """
    Basic test data for a generic test case.
    """
    filename = "test_attachment.pdf"
    file = SimpleUploadedFile(
        name=filename, content=b"test", content_type="application/pdf"
    )
    attachment = TestGenericAttachmentModel.objects.create(file_attachment=file)
    attachment_safedelete = TestGenericSafeDeleteAttachmentModel.objects.create(
        file_attachment=file
    )
    private_fieldfile = attachment.file_attachment
    scan: FileScanStatus = file_scan_status_factory(
        content_object=attachment,
        filepath=attachment.file_attachment.name,
        filefield_field_name="file_attachment",
    )
    return {
        "attachment": attachment,
        "attachment_safedelete": attachment_safedelete,
        "private_fieldfile": private_fieldfile,
        "scan": scan,
    }


@override_settings(FLAG_FILE_SCAN=False)
@pytest.mark.django_db
def test_filescan_pending(django_db_setup, generic_test_data):
    """
    FileScans that have not been scanned are pending.
    """
    scan = generic_test_data["scan"]
    assert scan.scanned_at is None
    assert scan.scan_result() == FileScanResult.PENDING


@override_settings(FLAG_FILE_SCAN=False)
@pytest.mark.django_db
def test_filescan_safe(django_db_setup, generic_test_data):
    """
    Files scanned as "safe" are handled correctly: not deleted.
    """
    attachment = generic_test_data["attachment"]
    with patch("requests.post") as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "success": True,
            "data": {
                "result": [
                    {
                        "name": attachment.file_attachment.name,
                        "is_infected": False,
                        "viruses": [],
                    }
                ]
            },
        }
        with patch("filescan.models.async_task") as mock_async_task:
            scan = schedule_file_for_virus_scanning(attachment, "file_attachment")
            if not scan:
                pytest.fail()

            # Verify that the task scheduler was invoked with correct arguments
            args, _ = mock_async_task.call_args
            scan_task, scan_pk = args
            assert scan_task == _scan_file_task
            assert scan_pk == scan.pk

            _scan_file_task(scan_pk)

            scan.refresh_from_db()
            assert scan.scan_result() == FileScanResult.SAFE
            # FieldFile (attachment.file_attachment) is truthy if it contains a reference to a file
            assert attachment.file_attachment
            assert os.path.isfile(attachment.file_attachment.path)
            assert scan.file_deleted_at is None


@override_settings(FLAG_FILE_SCAN=False)
@pytest.mark.django_db
def test_filescan_unsafe(
    django_db_setup,
    generic_test_data,
):
    """
    Files scanned as "unsafe" are handled correctly: deleted.
    """
    attachment = generic_test_data["attachment"]
    with patch("requests.post") as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "success": True,
            "data": {
                "result": [
                    {
                        "name": attachment.file_attachment.name,
                        "is_infected": True,
                        "viruses": ["Some_virus.exe"],
                    }
                ]
            },
        }
        with patch("filescan.models.async_task") as mock_async_task:
            scan = schedule_file_for_virus_scanning(attachment, "file_attachment")
            if not scan:
                pytest.fail()

            # Save the filepath before any operations are done to the file
            absolute_path = attachment.file_attachment.path

            # Verify that the task scheduler was invoked with correct arguments
            args, _ = mock_async_task.call_args
            scan_task, scan_pk = args
            assert scan_task == _scan_file_task
            assert scan_pk == scan.pk

            _scan_file_task(scan_pk)

            scan.refresh_from_db()
            attachment.refresh_from_db()
            assert scan.scan_result() == FileScanResult.UNSAFE
            assert not attachment.file_attachment
            assert (
                not attachment.file_attachment.name
            )  # can be empty string or None depending on test flow
            assert not os.path.isfile(absolute_path)
            assert scan.file_deleted_at is not None


@override_settings(FLAG_FILE_SCAN=False)
@pytest.mark.django_db
def test_file_deletion(
    django_db_setup,
    generic_test_data,
):
    """
    File deletion deletes the actual file, and sets FileField value to NULL.
    """
    attachment = generic_test_data["attachment"]
    scan = generic_test_data["scan"]
    absolute_path = attachment.file_attachment.path

    # FieldFile (attachment.attachment) is truthy if it contains a reference to a file
    assert attachment.file_attachment
    # FieldFile.name contains a value if FieldFile contains a reference to a file
    assert attachment.file_attachment.name is not None
    assert os.path.isfile(absolute_path)
    assert scan.file_deleted_at is None

    _delete_infected_file(
        scan,
    )

    attachment.refresh_from_db()
    assert not attachment.file_attachment
    assert (
        not attachment.file_attachment.name
    )  # can be empty string or None depending on test flow
    assert not os.path.isfile(absolute_path)
    assert scan.file_deleted_at is not None


@override_settings(FLAG_FILE_SCAN=False)
@pytest.mark.django_db
def test_private_field_file_open(
    django_db_setup,
    generic_test_data,
    file_scan_status_factory,
):
    """
    File in a PrivateFileField is only allowed to be opened if the file has been
    successfully scanned and found to be safe.
    """
    attachment = generic_test_data["attachment"]
    private_fieldfile: PrivateFieldFile = generic_test_data["private_fieldfile"]

    # File must be allowed to be opened for reading if feature flag is off
    with override_settings(FLAG_FILE_SCAN=False):
        try:
            assert private_fieldfile.open()
        except (FileScanPendingError, FileUnsafeError, FileScanError):
            pytest.fail(
                "An error related to file scanning was raised when feature flag is off"
            )

    # File has not yet been scanned --> open() method must raise an error
    _scan_status_pending: FileScanStatus = generic_test_data["scan"]  # noqa: F841
    with override_settings(FLAG_FILE_SCAN=True):
        with pytest.raises(FileScanPendingError):
            private_fieldfile.open()

    # File has been found safe --> it can be read
    _scan_status_safe: FileScanStatus = file_scan_status_factory(  # noqa: F841
        content_object=attachment,
        filepath=attachment.file_attachment.name,
        filefield_field_name="file_attachment",
        scanned_at=timezone.now(),
    )
    with override_settings(FLAG_FILE_SCAN=True):
        assert private_fieldfile.open()

    # File has been found unsafe --> open() method must raise an error
    _scan_status_unsafe: FileScanStatus = file_scan_status_factory(  # noqa: F841
        content_object=attachment,
        filepath=attachment.file_attachment.name,
        filefield_field_name="file_attachment",
        file_deleted_at=timezone.now(),
    )
    with override_settings(FLAG_FILE_SCAN=True):
        with pytest.raises(FileUnsafeError):
            private_fieldfile.open()

    # Filescan was not successful --> open() method must raise an error
    _scan_status_error: FileScanStatus = file_scan_status_factory(  # noqa: F841
        content_object=attachment,
        filepath=attachment.file_attachment.name,
        filefield_field_name="file_attachment",
        error_message="error message",
    )
    with override_settings(FLAG_FILE_SCAN=True):
        with pytest.raises(FileScanError):
            private_fieldfile.open()


@override_settings(FLAG_FILE_SCAN=False)
@pytest.mark.django_db
def test_safedelete_delete_does_not_trigger_filescan(
    django_db_setup, generic_test_data
):
    """
    Instances that inherit from safedelete.models.SafeDelete should not trigger
    filescans when their delete operation is invoked.
    """
    attachment_safedelete = generic_test_data["attachment_safedelete"]

    with override_settings(FLAG_FILE_SCAN=True):
        attachment_safedelete.delete()

    content_type = ContentType.objects.get_for_model(attachment_safedelete)
    assert not FileScanStatus.objects.filter(
        content_type=content_type, object_id=attachment_safedelete.pk
    ).exists()
