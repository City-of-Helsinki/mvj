from typing import Any

from django.core.files.storage import FileSystemStorage
from django.db import models

# Django docs poks: https://docs.djangoproject.com/en/5.1/topics/files/#file-storage
custom_fs = FileSystemStorage(location="attachments", base_url="/attachments/")


class CustomStorageFileFieldMixin:
    def __init__(self, storage=custom_fs, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.storage = storage


class CustomFileField(CustomStorageFileFieldMixin, models.FileField): ...
