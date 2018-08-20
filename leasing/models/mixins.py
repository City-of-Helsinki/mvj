from django.db import models
from django.utils.translation import ugettext_lazy as _
from safedelete.models import SafeDeleteModel


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Time created"))
    modified_at = models.DateTimeField(auto_now=True, verbose_name=_("Time modified"))

    class Meta:
        abstract = True


class TimeStampedSafeDeleteModel(TimeStampedModel, SafeDeleteModel):
    class Meta:
        abstract = True


class NameModel(models.Model):
    name = models.CharField(verbose_name=_("Name"), max_length=255)

    class Meta:
        abstract = True
        ordering = ['name']

    def __str__(self):
        return self.name


class ArchivableModel(models.Model):
    # In Finnish: Arkistoitu
    archived_at = models.DateTimeField(verbose_name=_("Time archived"), null=True, blank=True)
    # In Finnish: Huomautus (arkistointi)
    archived_note = models.TextField(verbose_name=_("Archived note"), null=True, blank=True)

    def is_archived(self):
        return bool(self.archived_at)

    class Meta:
        abstract = True
