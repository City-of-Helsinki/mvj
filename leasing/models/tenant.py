from django.db import models
from django.utils.translation import ugettext_lazy as _

from leasing.models import Lease
from leasing.models.contact import Contact
from leasing.models.mixins import TimestampedModelMixin


class Tenant(TimestampedModelMixin):
    lease = models.ForeignKey(
        Lease,
        related_name="tenants",
        on_delete=models.CASCADE,
    )
    contact = models.ForeignKey(
        Contact,
        related_name="tenants",
        on_delete=models.CASCADE,
    )
    contact_contact = models.ForeignKey(
        Contact,
        related_name="tenant_contacts",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    billing_contact = models.ForeignKey(
        Contact,
        related_name="tenant_billing_contacts",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    share_numerator = models.IntegerField(
        default=1,
        verbose_name=_("Numerator for the share of the rent"),
    )
    share_denominator = models.IntegerField(
        default=1,
        verbose_name=_("Denominator for the share of the rent"),
    )

    def get_billing_contact(self):
        return self.billing_contact if self.billing_contact else self.contact

    def __str__(self):
        return 'tenant contact: {} lease: {} '.format(self.contact, self.lease)
