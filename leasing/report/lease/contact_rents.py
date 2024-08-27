from decimal import ROUND_HALF_UP, Decimal

from django import forms
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError

from leasing.models import Contact, Lease
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
                "tenants__tenantcontact_set__contact",
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
            contacts_tenant = tenant_shares.get(contact)
            if contacts_tenant is not None:
                # One tenant can have multiple contacts, one tenant has only one rent share
                rent_share = next(iter(contacts_tenant.keys()))
                tenant_rent_share_portion = Decimal(
                    rent_share.share_numerator / rent_share.share_denominator
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
