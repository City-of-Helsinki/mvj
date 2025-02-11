from typing import Any

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.db import models
from django.db.models.fields.files import FieldFile

from file_operations.errors import FileScanError, FileScanPendingError, FileUnsafeError


class PrivateFileSystemStorage(FileSystemStorage):
    """
    Private files are stored in a location separate from the usual media root.
    """

    def __init__(self) -> None:
        # Raise an error if the PRIVATE_FILES_LOCATION setting is not set
        # To avoid resolving the location as the MEDIA_ROOT by default
        if len(settings.PRIVATE_FILES_LOCATION) == 0:
            raise ValueError("PRIVATE_FILES_LOCATION setting is not set")
        super().__init__(location=settings.PRIVATE_FILES_LOCATION, base_url=None)


class PrivateFieldFile(FieldFile):
    def open(self, mode="rb"):
        """
        Private files require a successful virus scan with a clean result before they can be opened.
        """
        file_scans_are_enabled = getattr(settings, "FLAG_FILE_SCAN", False) is True
        if file_scans_are_enabled is False:
            # File scanning feature is not enabled, all files should be allowed
            # to be read
            return super().open(mode)

        from file_operations.enums import FileScanResult
        from file_operations.models.filescan import FileScanStatus

        filescan_result = FileScanStatus.filefield_latest_scan_result(self.instance)

        if filescan_result == FileScanResult.SAFE:
            return super().open(mode)
        elif filescan_result == FileScanResult.PENDING:
            raise FileScanPendingError()
        elif filescan_result == FileScanResult.UNSAFE:
            raise FileUnsafeError()
        elif filescan_result == FileScanResult.ERROR:
            raise FileScanError()


class PrivateFileField(models.FileField):
    attr_class = PrivateFieldFile

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.storage = PrivateFileSystemStorage()
