from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext_lazy as _
from enumfields import EnumField

from leasing.enums import DecisionType
from leasing.models.mixins import TimestampedModelMixin


class Decision(TimestampedModelMixin):
    lease = models.ForeignKey('leasing.Lease', related_name="decisions", on_delete=models.PROTECT)
    name = models.CharField(verbose_name=_("Name"), null=True, blank=True, max_length=2048)
    date = models.DateField(verbose_name=_("Date"), null=True, blank=True)
    article = models.CharField(verbose_name=_("Article"), null=True, blank=True, max_length=255)
    type = EnumField(DecisionType, verbose_name=_("Type"), max_length=255)
    type_description = models.CharField(verbose_name=_("Type description"), null=True, blank=True, max_length=255)
    decision_maker = models.CharField(verbose_name=_("Decision-maker"), null=True, blank=True, max_length=255)
    link = models.CharField(verbose_name=_("Link"), null=True, blank=True, max_length=2048)
    abstract = models.CharField(verbose_name=_("Abstract"), null=True, blank=True, max_length=4096)
    added_by = models.ForeignKey(User, null=True, blank=True)
