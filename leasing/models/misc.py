from django.db import models
from django.utils.translation import ugettext_lazy as _

__all__ = (
    "PhoneNumber",
)


class PhoneNumber(models.Model):

    number = models.CharField(
        verbose_name=_("Phone number"),
        max_length=255,
        blank=False,
    )
