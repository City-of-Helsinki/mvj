from typing import Any

from django.db import models


class CleansOnSave(models.Model):
    class Meta:
        abstract = True

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.clean()
        super().save(*args, **kwargs)
