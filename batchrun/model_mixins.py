from typing import Any

from django.db import models
from django.utils.translation import ugettext_lazy as _
from safedelete.models import SafeDeleteModel


class CleansOnSave(models.Model):
    class Meta:
        abstract = True

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.clean()
        super().save(*args, **kwargs)


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_('creation time'))
    modified_at = models.DateTimeField(
        auto_now=True, verbose_name=_('modification time'))

    class Meta:
        abstract = True


class TimeStampedSafeDeleteModel(TimeStampedModel, SafeDeleteModel):
    class Meta:
        abstract = True
