from django.contrib.auth.models import User
from django.db import models, transaction
from django.db.models import Max
from django.utils.translation import ugettext_lazy as _
from enumfields import EnumField

from leasing.enums import (
    LEASE_IDENTIFIER_DISTRICT, LEASE_IDENTIFIER_MUNICIPALITY, LEASE_IDENTIFIER_TYPE, LeaseConditionType, LeaseState)
from leasing.models import Application
from leasing.models.mixins import TimestampedModelMixin


class LeaseIdentifier(models.Model):
    type = models.CharField(verbose_name=_("Type"), max_length=2, choices=LEASE_IDENTIFIER_TYPE)
    municipality = models.CharField(verbose_name=_("Municipality"), max_length=1,
                                    choices=LEASE_IDENTIFIER_MUNICIPALITY)
    district = models.CharField(verbose_name=_("District"), max_length=2, choices=LEASE_IDENTIFIER_DISTRICT)
    sequence = models.IntegerField(verbose_name=_("Sequence number"))

    class Meta:
        unique_together = ('type', 'municipality', 'district', 'sequence')

    def __str__(self):
        return '{}{}{}-{}'.format(self.type, self.municipality, self.district, self.sequence)


class Lease(TimestampedModelMixin):
    application = models.ForeignKey(Application, null=True, blank=True)
    is_reservation = models.BooleanField(verbose_name=_("Is a reservation?"), default=False)
    state = EnumField(LeaseState, verbose_name=_("State"), max_length=255)
    identifier_type = models.CharField(verbose_name=_("Lease identifier type"), choices=LEASE_IDENTIFIER_TYPE,
                                       null=True, blank=True, max_length=2)
    identifier_municipality = models.CharField(verbose_name=_("Lease identifier municipality"),
                                               choices=LEASE_IDENTIFIER_MUNICIPALITY, null=True, blank=True,
                                               max_length=1)
    identifier_district = models.CharField(verbose_name=_("Lease identifier district"),
                                           choices=LEASE_IDENTIFIER_DISTRICT, null=True, blank=True, max_length=2)
    identifier = models.OneToOneField(LeaseIdentifier, null=True, blank=True, on_delete=models.PROTECT)
    reasons = models.TextField(verbose_name=_("Reasons"), null=True, blank=True)
    detailed_plan = models.CharField(verbose_name=_("Detailed plan number"), null=True, blank=True,
                                     max_length=2048)
    detailed_plan_area = models.IntegerField(verbose_name=_("Detailed plan area in full square meters"), null=True,
                                             blank=True)
    preparer = models.ForeignKey(User, null=True, blank=True)
    is_billing_enabled = models.BooleanField(verbose_name=_("Is billing enabled?"), default=False)
    bills_per_year = models.IntegerField(verbose_name=_("Bills per year"), null=True, blank=True)
    start_date = models.DateField(verbose_name=_("Start date"), null=True, blank=True)
    end_date = models.DateField(verbose_name=_("End date"), null=True, blank=True)

    def __str__(self):
        return "id:{} identifier:{}".format(self.id, self.identifier)

    def identifier_string(self):
        if not self.identifier:
            return ''

        return str(self.identifier)

    @transaction.atomic
    def create_identifier(self):
        if not self.identifier_type or not self.identifier_municipality or not self.identifier_district:
            return

        max_sequence = LeaseIdentifier.objects.filter(
            type=self.identifier_type,
            municipality=self.identifier_municipality,
            district=self.identifier_district).aggregate(Max('sequence'))['sequence__max']

        if not max_sequence:
            max_sequence = 0

        lease_identifier = LeaseIdentifier.objects.create(
            type=self.identifier_type,
            municipality=self.identifier_municipality,
            district=self.identifier_district,
            sequence=max_sequence + 1)

        self.identifier = lease_identifier
        self.save()


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
