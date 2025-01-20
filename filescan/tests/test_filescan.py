import tempfile
from importlib import import_module
from typing import Type
from unittest.mock import patch

import pytest
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from conftest import FileScanStatusFactory
from filescan.models import (
    FileScanResult,
    FileScanStatus,
    _scan_file_task,
    schedule_file_for_virus_scanning,
)
from filescan.types import PlattaClamAvResponse
from plotsearch.models.plot_search import AreaSearchAttachment


# FIXME the attachments I generate in tests still use /media/ directory
#       Maybe Jukka's changes are required for the attachment creation to utilize the new root?
@pytest.fixture(scope="module")
def module_temp_dir():
    """
    Creates a temporary directory for the tests, sets that directory as the
    target directory for files to be scanned, and automatically deletes the
    directory and all the files within after all in the module tests are done.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        settings.PRIVATE_FILES_LOCATION = tmpdir
        settings.MEDIA_ROOT = (
            tmpdir  # TODO remove after Jukka's changes are integrated?
        )
        yield tmpdir


@pytest.mark.django_db
def test_filescan_pending(
    django_db_setup,
    module_temp_dir,
    file_scan_status_factory,
    area_search_attachment_factory,
):
    """FileScans that have not been scanned are pending"""
    filename = "test_attachment_1.pdf"
    file = SimpleUploadedFile(
        name=filename, content=b"test", content_type="application/pdf"
    )
    attachment: AreaSearchAttachment = area_search_attachment_factory(attachment=file)
    scan: FileScanStatus = file_scan_status_factory(
        content_object=attachment, filepath=attachment.attachment.name
    )
    assert scan.scan_result() == FileScanResult.PENDING


def async_task_as_sync(*args, **kwargs):
    return _scan_file_task


@pytest.mark.django_db
def test_filescan_safe(
    django_db_setup,
    module_temp_dir,
    area_search_attachment_factory,
):
    """Files scanned as "safe" are handled correctly: not deleted."""
    filename = "test_attachment_1.pdf"
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

            args, _ = mock_async_task.call_args
            scan_task, scan_pk = args

            assert scan_task == _scan_file_task
            assert scan_pk == scan.pk

            _scan_file_task(scan_pk)

    scan.refresh_from_db()
    assert scan.scan_result() == FileScanResult.SAFE


@pytest.mark.django_db
def test_filescan_unsafe(
    django_db_setup,
    module_temp_dir,
    area_search_attachment_factory,
):
    """Files scanned as "unsafe" are handled correctly: deleted."""
    filename = "test_attachment_1.pdf"
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

            args, _ = mock_async_task.call_args
            scan_task, scan_pk = args

            assert scan_task == _scan_file_task
            assert scan_pk == scan.pk

            _scan_file_task(scan_pk)

    scan.refresh_from_db()
    assert scan.scan_result() == FileScanResult.UNSAFE
