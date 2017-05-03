from django.db import models
from django.utils.translation import ugettext_lazy as _

from leasing.models.mixins import TimestampedModelMixin


class Contact(TimestampedModelMixin):
    name = models.CharField(verbose_name=_("Name"), null=True, blank=True, max_length=255)
    address = models.CharField(verbose_name=_("Address"), null=True, blank=True, max_length=2048)
    billing_address = models.CharField(verbose_name=_("Billing address"), null=True, blank=True,
                                       max_length=2048)
    electronic_billing_details = models.CharField(verbose_name=_("Electronic billing details"), null=True, blank=True,
                                                  max_length=2048)
    email = models.EmailField(verbose_name=_("Email address"), null=True, blank=True)
    phone = models.CharField(verbose_name=_("Phone number"), null=True, blank=True, max_length=255)

    organization_name = models.CharField(verbose_name=_("Organization name"), null=True, blank=True, max_length=255)
    organization_address = models.CharField(verbose_name=_("Organization address"), null=True, blank=True,
                                            max_length=255)
    organization_is_company = models.BooleanField(verbose_name=_("Is organization a company"), default=False)
    organization_id = models.CharField(verbose_name=_("Organization id"), null=True, blank=True, max_length=255)
    organization_revenue = models.CharField(verbose_name=_("Organization revenue"), null=True, blank=True,
                                            max_length=255)

    def __str__(self):
        parts = []

        if self.name:
            parts.append(self.name)

        if self.organization_name:
            parts.append(self.organization_name)

        return ' '.join(parts)
