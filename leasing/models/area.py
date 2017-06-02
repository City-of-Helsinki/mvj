from django.contrib.gis.db import models

from leasing.models.mixins import TimestampedModelMixin


class Area(TimestampedModelMixin):
    name = models.CharField(max_length=255)
    mpoly = models.MultiPolygonField(srid=3879)

    notes = models.ManyToManyField('leasing.Note', blank=True)

    def __str__(self):
        return self.name if self.name else ''
