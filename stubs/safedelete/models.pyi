import datetime

from django.db import models
from safedelete.managers import (
    SafeDeleteAllManager,
    SafeDeleteDeletedManager,
    SafeDeleteManager,
)

class SafeDeleteModel(models.Model):
    deleted: datetime.datetime | None
    objects: SafeDeleteManager
    all_objects: SafeDeleteAllManager
    deleted_objects: SafeDeleteDeletedManager
