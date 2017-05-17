from django.db import models
from django.utils.translation import ugettext_lazy as _
from enumfields import EnumField

from leasing.enums import ApplicationState, ApplicationType, ShortTermReason
from leasing.models.mixins import TimestampedModelMixin


class Application(TimestampedModelMixin):
    state = EnumField(ApplicationState, verbose_name=_("Application state"), max_length=255,
                      default=ApplicationState.UNHANDLED)
    type = EnumField(ApplicationType, verbose_name=_("Application type"), max_length=255)
    is_open = models.BooleanField(verbose_name=_("Is an open application"), default=False)
    reasons = models.TextField(verbose_name=_("Application reasons"), null=True, blank=True)

    lease_start_date = models.DateField(verbose_name=_("Lease start date"), null=True, blank=True)
    lease_end_date = models.DateField(verbose_name=_("Lease end date"), null=True, blank=True)
    lease_is_reservation = models.BooleanField(verbose_name=_("Lease is a reservation"), default=False)
    lease_is_short_term = models.BooleanField(verbose_name=_("Lease is short term"), default=False)
    lease_is_long_term = models.BooleanField(verbose_name=_("Lease is long term"), default=False)
    lease_short_term_reason = EnumField(ShortTermReason, verbose_name=_("Reason for short term lease"), null=True,
                                        blank=True, max_length=255)

    organization_name = models.CharField(verbose_name=_("Organization name"), null=True, blank=True, max_length=255)
    organization_address = models.CharField(verbose_name=_("Organization address"), null=True, blank=True,
                                            max_length=255)
    organization_is_company = models.BooleanField(verbose_name=_("Is organization a company"), default=False)
    organization_id = models.CharField(verbose_name=_("Organization id"), null=True, blank=True, max_length=255)
    organization_revenue = models.CharField(verbose_name=_("Organization revenue"), null=True, blank=True,
                                            max_length=255)

    contact_name = models.CharField(verbose_name=_("Contact name"), null=True, blank=True, max_length=255)
    contact_address = models.CharField(verbose_name=_("Contacts address"), null=True, blank=True, max_length=2048)
    contact_billing_address = models.CharField(verbose_name=_("Contacts billing address"), null=True, blank=True,
                                               max_length=2048)
    contact_electronic_billing = models.CharField(verbose_name=_("Contacts electronic billing details"), null=True,
                                                  blank=True, max_length=2048)
    contact_email = models.EmailField(verbose_name=_("Contacts email address"), null=True, blank=True)
    contact_phone = models.CharField(verbose_name=_("Contacts phone number"), null=True, blank=True, max_length=255)

    land_area = models.IntegerField(verbose_name=_("Land area in full square meters"), null=True, blank=True)
    land_id = models.CharField(verbose_name=_("Land id"), null=True, blank=True, max_length=255)
    land_address = models.CharField(verbose_name=_("Land address"), null=True, blank=True, max_length=2048)
    land_map_link = models.CharField(verbose_name=_("Land map link"), null=True, blank=True, max_length=2048)

    areas = models.ManyToManyField('leasing.Area', blank=True)
    notes = models.ManyToManyField('leasing.Note', blank=True)

    def __str__(self):
        return '#{id} {type} {contact_person}'.format(id=self.id, type=self.type.label,
                                                      contact_person=str(self.contact_name))

    def as_contact(self):
        from .contact import Contact

        field_names = [
            'contact_name',
            'contact_address',
            'contact_billing_address',
            'contact_electronic_billing',
            'contact_email',
            'contact_phone',
            'organization_name',
            'organization_address',
            'organization_is_company',
            'organization_id',
            'organization_revenue',
        ]

        values = {key.replace('contact_', ''): getattr(self, key) for key in field_names}
        values['electronic_billing_details'] = values.pop('electronic_billing')

        return Contact(**values)
