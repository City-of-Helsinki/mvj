import tempfile
from unittest.mock import patch

import pytest
from django.conf import settings
from django.contrib.contenttypes.models import ContentType

from filescan.models import FileScanResult, FileScanStatus, scan_file_task
from plotsearch.models.plot_search import (
    AreaSearchAttachment,
    get_area_search_attachment_upload_to,
)


@pytest.fixture(scope="module")
def module_temp_dir():
    """
    Creates a temporary directory for the tests, sets that directory as the
    target directory for files to be scanned, and automatically deletes the
    directory and all the files within after all in the module tests are done.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        settings.PRIVATE_FILES_LOCATION = tmpdir
        yield tmpdir


# TODO is this needed for all tests, or only for some?
#      If only for some, remove autouse
@pytest.fixture(autouse=True)
def patch_filescan_save():
    """
    Patches the save() method of all FileScanStatus instances in this test file,
    to have more control over when the scan is triggered during tests.
    """

    def mock_save_without_task(self, *args, **kwargs):
        super(FileScanStatus, self).save(*args, **kwargs)

    with patch(
        "filescan.models.FileScanStatus.save", new=mock_save_without_task
    ) as mock_save:
        yield mock_save


@pytest.mark.django_db
def test_filescan_pending(
    django_db_setup,
    module_temp_dir,  # TODO needed?
    file_scan_status_factory,
    area_search_attachment_factory,
):
    """FileScans that have not been scanned are pending"""
    # TODO reasonable properties for attachment to be used in tests
    filename = "test_attachment_1.pdf"

    attachment: AreaSearchAttachment = area_search_attachment_factory(
        name=filename,
    )

    filepath = get_area_search_attachment_upload_to(
        instance=attachment, filename=filename
    )
    scan = file_scan_status_factory(
        content_object=attachment, filepath=attachment.attachment
    )
    # We mocked the scan task out of the save method, so it should not have been run
    scan.scan_result = FileScanResult.PENDING


@pytest.mark.django_db
def test_filescan_safe(django_db_setup):
    """Files scanned as "safe" are handled correctly: not deleted."""
    # TODO
    pass


@pytest.mark.django_db
def test_filescan_unsafe(django_db_setup):
    """Files scanned as "unsafe" are handled correctly: deleted."""
    # TODO
    pass


@pytest.mark.django_db
def test_filescan_details_are_obfuscated(django_db_setup):
    """Filename and metadata are masked before sending the file for scanning."""
    # TODO
    pass
