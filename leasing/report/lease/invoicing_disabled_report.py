from django import forms
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from leasing.enums import LeaseState, RentType
from leasing.models import Lease
from leasing.report.report_base import ReportBase

from leasing.models import ServiceUnit


def get_lease_id(obj):
    return obj.get_identifier_string()


class LeaseInvoicingDisabledReport(ReportBase):
    name = _("Leases where invoicing is disabled")
    description = _("Shows active leases where invoicing is not enabled")
    slug = "lease_invoicing_disabled"
    input_fields = {
        "service_unit": forms.ModelChoiceField(
            label=_("Palvelukokonaisuus"), required=False, queryset=ServiceUnit.objects.all()
        ),
    }
    output_fields = {
        "lease_id": {"source": get_lease_id, "label": _("Lease id")},
        "start_date": {"label": _("Start date"), "format": "date"},
        "end_date": {"label": _("End date"), "format": "date"},
    }

    def get_data(self, input_data):
        today = timezone.now().date()

        qs = (
            Lease.objects.filter(
                Q(end_date__isnull=True) | Q(end_date__gte=today),
                start_date__isnull=False,
                state__in=[
                    LeaseState.LEASE,
                    LeaseState.SHORT_TERM_LEASE,
                    LeaseState.LONG_TERM_LEASE,
                ],
                is_invoicing_enabled=False,
            )
            .select_related(
                "identifier",
                "identifier__type",
                "identifier__district",
                "identifier__municipality",
            )
            .prefetch_related("rents")
            .order_by("start_date", "end_date")
        )

        if input_data["service_unit"].id:
            qs = qs.filter(service_unit=input_data["service_unit"].id)

        leases = []
        for lease in qs:
            free = True
            for rent in lease.rents.all():
                if rent.type is not RentType.FREE:
                    free = False
                    break
            if not free:
                leases.append(lease)

        return leases
