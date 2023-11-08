from auditlog.registry import auditlog
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy
from enumfields import EnumField

from field_permissions.registry import field_permissions
from leasing.enums import TenantContactType
from leasing.models import Contact, RentIntendedUse
from leasing.models.mixins import TimeStampedSafeDeleteModel


class Tenant(TimeStampedSafeDeleteModel):
    """
    In Finnish: Vuokralainen
    """

    lease = models.ForeignKey(
        "leasing.Lease",
        verbose_name=_("Lease"),
        related_name="tenants",
        on_delete=models.PROTECT,
    )

    # In Finnish: Jaettava / Osoittaja
    share_numerator = models.PositiveIntegerField(verbose_name=_("Numerator"))

    # In Finnish: Jakaja / Nimittäjä
    share_denominator = models.PositiveIntegerField(verbose_name=_("Denominator"))

    # In Finnish: Viite
    reference = models.CharField(
        verbose_name=_("Reference"), null=True, blank=True, max_length=35
    )

    contacts = models.ManyToManyField(
        Contact, through="leasing.TenantContact", related_name="tenants"
    )

    # TODO: Add start and end dates?

    recursive_get_related_skip_relations = ["lease", "contacts"]

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Tenant")
        verbose_name_plural = pgettext_lazy("Model name", "Tenants")

    def __str__(self):
        return "Tenant id: {} share: {}/{}".format(
            self.id, self.share_numerator, self.share_denominator
        )

    def get_tenantcontacts_for_period(self, contact_type, start_date, end_date):
        if not end_date:
            range_filter = Q(Q(end_date=None) | Q(end_date__gte=start_date))
        else:
            range_filter = Q(
                Q(Q(end_date=None) | Q(end_date__gte=start_date))
                & Q(Q(start_date=None) | Q(start_date__lte=end_date))
            )

        tenantcontacts = (
            self.tenantcontact_set.filter(type=contact_type)
            .filter(range_filter)
            .order_by("-start_date")
        )

        return tenantcontacts

    def get_tenant_tenantcontacts(self, start_date, end_date):
        return self.get_tenantcontacts_for_period(
            TenantContactType.TENANT, start_date, end_date
        )

    def get_billing_tenantcontacts(self, start_date, end_date):
        billing_contacts = self.get_tenantcontacts_for_period(
            TenantContactType.BILLING, start_date, end_date
        )

        if billing_contacts.count() > 0:
            return billing_contacts
        else:
            return self.get_tenant_tenantcontacts(start_date, end_date)

    def get_rent_share_by_intended_use(self, intended_use):
        try:
            return self.rent_shares.get(intended_use=intended_use)
        except TenantRentShare.DoesNotExist:
            # TODO: Better error handling
            return None


class TenantContact(TimeStampedSafeDeleteModel):
    type = EnumField(TenantContactType, max_length=255)
    tenant = models.ForeignKey(
        Tenant, verbose_name=_("Tenant"), on_delete=models.PROTECT
    )
    contact = models.ForeignKey(
        Contact, verbose_name=_("Contact"), on_delete=models.PROTECT
    )

    # In Finnish: Alkupvm
    start_date = models.DateField(verbose_name=_("Start date"))

    # In Finnish: Loppupvm
    end_date = models.DateField(verbose_name=_("End date"), null=True, blank=True)

    recursive_get_related_skip_relations = ["tenant"]

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Tenant contact")
        verbose_name_plural = pgettext_lazy("Model name", "Tenant contacts")

    def __str__(self):
        return "TenantContact id: {} contact: {} period: {} - {}".format(
            self.id, self.contact, self.start_date, self.end_date
        )

    @property
    def date_range(self):
        return self.start_date, self.end_date


class TenantRentShare(TimeStampedSafeDeleteModel):
    """
    In Finnish: Laskuosuus
    """

    tenant = models.ForeignKey(
        Tenant,
        verbose_name=_("Tenant"),
        related_name="rent_shares",
        on_delete=models.PROTECT,
    )

    # In Finnish: Käyttötarkoitus
    intended_use = models.ForeignKey(
        RentIntendedUse,
        verbose_name=_("Intended use"),
        related_name="+",
        on_delete=models.PROTECT,
    )

    # In Finnish: Jaettava / Osoittaja (Laskuosuus)
    share_numerator = models.PositiveIntegerField(
        verbose_name=_("Rent share numerator")
    )

    # In Finnish: Jakaja / Nimittäjä (Laskuosuus)
    share_denominator = models.PositiveIntegerField(
        verbose_name=_("Rent share denominator")
    )

    recursive_get_related_skip_relations = ["tenant"]

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Tenant rent share")
        verbose_name_plural = pgettext_lazy("Model name", "Tenant rent shares")


auditlog.register(Tenant)
auditlog.register(TenantContact)
auditlog.register(TenantRentShare)

field_permissions.register(Tenant, exclude_fields=["lease", "invoicerow"])
field_permissions.register(TenantContact, exclude_fields=["tenant"])
field_permissions.register(TenantRentShare, exclude_fields=["tenant"])
