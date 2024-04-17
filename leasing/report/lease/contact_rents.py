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
        "start_date": {"label": "Start date"},
        "end_date": {"label": "End date"},
        "address": {"label": _("Address"), "source": get_address, "width": 20},
        "tenants": {"label": _("Tenants"), "source": get_tenants, "width": 40},
        "rent_amount": {
            "label": _("Rent amount"),
            "source": "_report__rent_for_period",
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
                Q(end_date__isnull=True) | Q(end_date__gte=input_data["start_date"]),
                tenants__contacts=contact,
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
            rent_for_period = lease.calculate_rent_amount_for_period(
                input_data["start_date"], input_data["end_date"]
            )
            lease._report__rent_for_period = (
                rent_for_period.get_total_amount().quantize(
                    Decimal(".01"), rounding=ROUND_HALF_UP
                )
            )

        return leases
