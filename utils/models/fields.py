from typing import Any

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.db import models
from django.db.models.fields.files import FieldFile


class UnsafeFileError(Exception):
    """Raised when a file is attempted to be opened but is not marked to be
    safe by FileScanStatus."""

    pass


class PrivateFileSystemStorage(FileSystemStorage):
    def __init__(self) -> None:
        # base_url is not needed, but it defaults to MEDIA_URL if not explicitly set
        super().__init__(location=settings.PRIVATE_FILES_LOCATION, base_url=None)


class PrivateFieldFile(FieldFile):
    def open(self, mode="rb"):
        if (
            settings.FLAG_FILE_SCAN is True
            and self._is_file_scanned_and_safe() is False
        ):
            raise UnsafeFileError("Opening this file is not allowed.")
        return super().open(mode)

    def _is_file_scanned_and_safe(self) -> bool:
        from filescan.models import FileScanStatus

        return FileScanStatus.is_file_scanned_and_safe(self.instance)


class PrivateFileField(models.FileField):
    attr_class = PrivateFieldFile

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.storage = PrivateFileSystemStorage()

    def pre_save(self, instance: models.Model, add: bool) -> FieldFile:
        file = super().pre_save(instance, add)

        if settings.FLAG_FILE_SCAN is True:
            from filescan.models import schedule_file_for_virus_scanning

            schedule_file_for_virus_scanning(
                file_model_instance=instance, file_field_name=self.attname
            )

        return file
