from django.db import models
from django.utils.translation import ugettext_lazy as _

from leasing.models import Lease
from leasing.models.contact import Contact
from leasing.models.mixins import TimestampedModelMixin


class Tenant(TimestampedModelMixin):
    lease = models.ForeignKey(Lease, related_name="tenants", on_delete=models.CASCADE)
    contact = models.ForeignKey(Contact, related_name="tenants", on_delete=models.CASCADE)
    contact_contact = models.ForeignKey(Contact, related_name="tenant_contacts", null=True, blank=True,
                                        on_delete=models.CASCADE)
    billing_contact = models.ForeignKey(Contact, related_name="tenant_billing_contacts", null=True, blank=True,
                                        on_delete=models.CASCADE)
    share = models.DecimalField(verbose_name=_("Share of the rent"), max_digits=7, decimal_places=6)
