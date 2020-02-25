from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from leasing.enums import LeaseState
from leasing.models import Lease
from leasing.report.report_base import ReportBase


def get_lease_id(obj):
    return obj.get_identifier_string()


class LeaseInvoicingDisabledReport(ReportBase):
    name = _('Leases where invoicing is disabled')
    description = _('Shows active leases where invoicing is not enabled')
    slug = 'lease_invoicing_disabled'
    output_fields = {
        'lease_id': {
            'source': get_lease_id,
            'label': _('Lease id'),
        },
        'start_date': {
            'label': _('Start date'),
            'format': 'date',
        },
        'end_date': {
            'label': _('End date'),
            'format': 'date',
        },
    }

    def get_data(self, input_data):
        today = timezone.now().date()

        return Lease.objects.filter(
            start_date__isnull=False,
            end_date__gte=today,
            state__in=[LeaseState.LEASE, LeaseState.SHORT_TERM_LEASE, LeaseState.LONG_TERM_LEASE],
            is_invoicing_enabled=False
        ).select_related(
            'identifier', 'identifier__type', 'identifier__district', 'identifier__municipality',
        ).order_by('start_date', 'end_date')
