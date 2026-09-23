from django.db import models
from django.utils.translation import gettext_lazy as _


# TODO use in relevant classes where timestamps are useful
class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Time created"))
    modified_at = models.DateTimeField(auto_now=True, verbose_name=_("Time modified"))

    class Meta:
        abstract = True
