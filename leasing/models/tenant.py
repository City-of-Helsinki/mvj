from auditlog.registry import auditlog
from django.db import models
from django.utils.translation import ugettext_lazy as _
from enumfields import EnumField

from leasing.enums import TenantContactType
from leasing.models import Contact
from leasing.models.mixins import TimeStampedSafeDeleteModel


class Tenant(TimeStampedSafeDeleteModel):
    """In Finnish: Vuokralainen"""
    lease = models.ForeignKey('leasing.Lease', verbose_name=_("Lease"), related_name='tenants',
                              on_delete=models.PROTECT)

    # In Finnish: Jaettava
    share_numerator = models.PositiveIntegerField(verbose_name=_("Numerator"))

    # In Finnish: Jakaja
    share_denominator = models.PositiveIntegerField(verbose_name=_("Denominator"))

    # In Finnish: Viite
    reference = models.CharField(verbose_name=_("Reference"), null=True, blank=True, max_length=255)

    contacts = models.ManyToManyField(Contact, through='leasing.TenantContact', related_name='tenants')


class TenantContact(TimeStampedSafeDeleteModel):
    type = EnumField(TenantContactType, max_length=255)
    tenant = models.ForeignKey(Tenant, verbose_name=_("Tenant"), on_delete=models.PROTECT)
    contact = models.ForeignKey(Contact, verbose_name=_("Contact"), on_delete=models.PROTECT)

    # In Finnish: Alkupvm
    start_date = models.DateField(verbose_name=_("Start date"))

    # In Finnish: Loppupvm
    end_date = models.DateField(verbose_name=_("End date"), null=True, blank=True)


auditlog.register(Tenant)
auditlog.register(TenantContact)
