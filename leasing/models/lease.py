from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext_lazy as _
from enumfields import EnumField

from leasing.enums import LeaseConditionType, LeaseState
from leasing.models import Application
from leasing.models.mixins import TimestampedModelMixin


class Lease(TimestampedModelMixin):
    application = models.ForeignKey(Application, null=True, blank=True)
    is_reservation = models.BooleanField(verbose_name=_("Is a reservation?"), default=False)
    state = EnumField(LeaseState, verbose_name=_("State"), max_length=255)
    lease_id = models.CharField(verbose_name=_("Lease id"), null=True, blank=True, max_length=255)
    reasons = models.TextField(verbose_name=_("Reasons"), null=True, blank=True)
    detailed_plan = models.CharField(verbose_name=_("Detailed plan number"), null=True, blank=True,
                                     max_length=2048)
    detailed_plan_area = models.IntegerField(verbose_name=_("Detailed plan area in full square meters"), null=True,
                                             blank=True)
    preparer = models.ForeignKey(User, null=True, blank=True)

    def __str__(self):
        return "id:{} lease_id:{}".format(self.id, self.lease_id)


class LeaseRealPropertyUnit(models.Model):
    lease = models.ForeignKey(Lease, related_name="real_property_units", on_delete=models.CASCADE)
    identification_number = models.CharField(verbose_name=_("Real property unit identification number"), null=True,
                                             blank=True, max_length=255)
    name = models.CharField(verbose_name=_("Name"), null=True, blank=True, max_length=2048)
    area = models.IntegerField(verbose_name=_("Area in full square meters"), null=True, blank=True)
    registry_date = models.DateField(verbose_name=_("Registry date"), null=True, blank=True)


class LeaseRealPropertyUnitAddress(models.Model):
    lease_property_unit = models.ForeignKey(LeaseRealPropertyUnit, related_name="addresses", on_delete=models.CASCADE)
    address = models.CharField(verbose_name=_("Address"), null=True, blank=True, max_length=2048)


class LeaseAdditionalField(models.Model):
    lease = models.ForeignKey(Lease, related_name="additional_fields", on_delete=models.CASCADE)
    name = models.CharField(verbose_name=_("Field name"), null=True, blank=True, max_length=2048)
    value = models.CharField(verbose_name=_("Field Value"), null=True, blank=True, max_length=2048)
    date = models.DateField(verbose_name=_("Date"), null=True, blank=True)
    requires_review = models.BooleanField(verbose_name=_("Requires review?"), default=False)
    reviewed_by = models.ForeignKey(User, null=True, blank=True)
    reviewed_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Time reviewed"))


class LeaseCondition(models.Model):
    lease = models.ForeignKey(Lease, related_name="conditions", on_delete=models.CASCADE)
    type = EnumField(LeaseConditionType, verbose_name=_("Condition type"), max_length=255)
    description = models.CharField(verbose_name=_("Description"), null=True, blank=True, max_length=2048)
    date = models.DateField(verbose_name=_("Date"), null=True, blank=True)
