from typing import Any

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.db import models


class PrivateFileSystemStorage(FileSystemStorage): ...  # noqa: E701


class PrivateFileField(models.FileField):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.storage = PrivateFileSystemStorage(
            location=settings.PRIVATE_FILES_LOCATION,
            base_url=None,
        )
