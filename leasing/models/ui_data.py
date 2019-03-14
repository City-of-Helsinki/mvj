from django.contrib.gis.db import models
from django.utils.translation import pgettext_lazy
from django.utils.translation import ugettext_lazy as _

from users.models import User

from .mixins import TimeStampedModel


class UiData(TimeStampedModel):
    user = models.ForeignKey(User, verbose_name=_("User"), related_name='+', null=True, blank=True,
                             on_delete=models.PROTECT)
    key = models.CharField(verbose_name=_("Key"), max_length=255)
    value = models.TextField(verbose_name=_("Value"))

    class Meta:
        verbose_name = pgettext_lazy("Model name", "UI Datum")
        verbose_name_plural = pgettext_lazy("Model name", "UI Data")
        unique_together = (('user', 'key'),)
        permissions = (
            ("edit_global_ui_data", "Can create, edit and delete global UI data"),
        )
