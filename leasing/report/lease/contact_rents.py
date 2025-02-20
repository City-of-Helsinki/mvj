import datetime
from decimal import ROUND_HALF_UP, Decimal

from django import forms
from django.db.models import Q, QuerySet
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError

from leasing.enums import TenantContactType
from leasing.models import Contact, Lease
from leasing.models.tenant import Tenant, TenantContact
from leasing.models.types import TenantShares
from leasing.report.lease.common_getters import (
    get_address,
    get_lease_area_identifier,
    get_lease_id,
    get_tenants,
)
from leasing.report.report_base import ReportBase


class ContactRentsReport(ReportBase):
    name = _("Contact rents")
    description = _(
        "Show all rent amounts from all of the leases the contact is a part of"
    )
    slug = "contact_rents"
    input_fields = {
        "start_date": forms.DateField(label=_("Start date"), required=True),
        "end_date": forms.DateField(label=_("End date"), required=True),
        "contact_id": forms.IntegerField(label=_("Contact identifier"), required=True),
    }
    output_fields = {
        "lease_id": {
            "label": _("Lease identifier"),
            "source": get_lease_id,
            "width": 13,
        },
        "lease_area_identifier": {
            "label": _("Lease area identifier"),
            "source": get_lease_area_identifier,
            "width": 20,
        },
        "start_date": {"label": _("Start date"), "format": "date"},
        "end_date": {"label": _("End date"), "format": "date"},
        "address": {"label": _("Address"), "source": get_address, "width": 20},
        "tenants": {"label": _("Tenants"), "source": get_tenants, "width": 40},
        "rent_amount": {
            "label": _("Rent amount"),
            "source": "_report__rent_for_period",
            "format": "money",
            "width": 13,
        },
        "rent_amount_for_contact": {
            "label": _("Rent amount for contact"),
            "source": "_report__tenants_rent_for_period",
            "format": "money",
            "width": 13,
        },
    }

    def get_data(self, input_data):
        try:
            contact = Contact.objects.get(pk=input_data["contact_id"])
        except Contact.DoesNotExist:
            raise ValidationError(_("Contact not found"))

        leases = (
            Lease.objects.filter(
                tenants__tenantcontact__type=TenantContactType.TENANT,
                tenants__contacts=contact,
                tenants__deleted__isnull=True,
                tenants__contacts__deleted__isnull=True,
            )
            .filter(
                Q(end_date__isnull=True) | Q(end_date__gte=input_data["start_date"]),
            )
            .select_related(
                "identifier",
                "identifier__type",
                "identifier__district",
                "identifier__municipality",
            )
            .prefetch_related(
                "lease_areas__addresses",
                "tenants__contacts",
                "tenants__tenantcontact_set__contact",
                "rents",
            )
            .distinct()
        )

        for lease in leases:
            date_range = (
                input_data["start_date"],
                input_data["end_date"],
            )
            rent_for_period = lease.calculate_rent_amount_for_period(*date_range)
            rent_total_amount_for_period = rent_for_period.get_total_amount()
            lease._report__rent_for_period = rent_total_amount_for_period.quantize(
                Decimal(".01"), rounding=ROUND_HALF_UP
            )

            tenant_shares = lease.get_tenant_shares_for_period(*date_range)
            tenant = self._get_tenant_from_tenant_shares(
                contact, lease, tenant_shares, date_range
            )

            if tenant is not None:
                # One Tenant can have multiple Contacts via TenantContact, one Tenant has only one rent share
                tenant_rent_share_portion = Decimal(
                    tenant.share_numerator / tenant.share_denominator
                )
                rent_of_single_tenant_for_period = (
                    rent_total_amount_for_period * tenant_rent_share_portion
                )
                lease._report__tenants_rent_for_period = (
                    rent_of_single_tenant_for_period.quantize(
                        Decimal(".01"), rounding=ROUND_HALF_UP
                    )
                )
            else:
                lease._report__tenants_rent_for_period = lease._report__rent_for_period

        return leases

    def _get_tenant_from_tenant_shares(
        self,
        contact: Contact,
        lease: Lease,
        tenant_shares: TenantShares,
        date_range: tuple[datetime.date, datetime.date],
    ) -> Tenant | None:
        """
        Get Tenant for the given Contact or for Contact & Lease from tenant_shares.
        If the contact is not directly found in tenant_shares, attempt to get the shared tenant
        with the billing contact. This is because only TenantContact.type `billing` contacts are
        included in tenant_shares, not TenantContact.type `tenant`.
        """
        # a Tenant from TenantContact.tenant of type TenantContactType.BILLING
        billing_contacts_tenant = tenant_shares.get(contact)
        if billing_contacts_tenant is not None:
            # Contact is in tenant_shares as it is of type `BILLING`
            tenant: Tenant | None = next(iter(billing_contacts_tenant.keys()))
            return tenant

        # `tenant_shares` only includes billing contacts as keys.
        # Attempt to get the Tenant for the contact if it is of type TENANT and
        # its Tenant is the same as one of the billing contacts.
        contacts_tenantcontacts: QuerySet[TenantContact] = contact.tenantcontact_set
        start_date, end_date = date_range
        tenantcontact_range_filter = Q(
            Q(Q(end_date=None) | Q(end_date__gte=start_date))
            & Q(Q(start_date=None) | Q(start_date__lte=end_date))
            & Q(deleted__isnull=True)
        )
        contacts_tenantcontact: TenantContact = contacts_tenantcontacts.filter(
            tenantcontact_range_filter,
            tenant__lease=lease,
            type=TenantContactType.TENANT,
        ).first()

        if not contacts_tenantcontact:
            # Contacts Tenant is not found in tenant_shares, edge case which "should not happen"
            return None

        # a Tenant from TenantContact.tenant of `type` TenantContactType.TENANT
        contacts_tenant: Tenant = contacts_tenantcontact.tenant
        all_tenant_periods = tenant_shares.values()
        # Look for the Contacts Tenant in all tenant periods
        for tenant_period in all_tenant_periods:
            if contacts_tenant in tenant_period:
                tenants = tenant_period.keys()
                tenant: Tenant | None = next(iter(tenants))
                return tenant

        return None
