from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.gis.db import models
from django.utils.translation import pgettext_lazy
from django.utils.translation import ugettext_lazy as _
from enumfields import EnumField

from leasing.enums import EmailLogType
from users.models import User

from .mixins import TimeStampedSafeDeleteModel


class EmailLog(TimeStampedSafeDeleteModel):
    """
    In Finnish: Sähköpostiloki
    """
    type = EnumField(EmailLogType, verbose_name=_("Email log type"), max_length=30)
    user = models.ForeignKey(User, related_name="emaillogs", verbose_name=_("User"), on_delete=models.PROTECT)
    text = models.TextField(verbose_name=_("Text"), null=True, blank=True)
    sent_at = models.DateTimeField(verbose_name=_("Time created"), null=True, blank=True)
    recipients = models.ManyToManyField(User)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Email log")
        verbose_name_plural = pgettext_lazy("Model name", "Email logs")
