from django.contrib.auth.models import User
from django.db import models

from leasing.models.mixins import TimestampedModelMixin


class Note(TimestampedModelMixin):
    title = models.CharField(max_length=255, null=True, blank=True)
    text = models.TextField(null=True, blank=True)
    author = models.ForeignKey(User, null=True, blank=True)

    def __str__(self):
        return self.title if self.title else ''
