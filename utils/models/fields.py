from typing import Any

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.db import models
from django.db.models.fields.files import FieldFile


class PrivateFileSystemStorage(FileSystemStorage):
    def __init__(self) -> None:
        # base_url is not needed, but it defaults to MEDIA_URL if not explicitly set
        super().__init__(location=settings.PRIVATE_FILES_LOCATION, base_url=None)


class PrivateFileField(models.FileField):
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

    # TODO accessor
