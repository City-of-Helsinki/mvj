from typing import Any

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.db import models


class PrivateFileSystemStorage(FileSystemStorage):
    def __init__(self) -> None:
        # base_url is not needed, but it defaults to MEDIA_URL if not explicitly set
        super().__init__(location=settings.PRIVATE_FILES_LOCATION, base_url=None)


class PrivateFileField(models.FileField):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.storage = PrivateFileSystemStorage()
