from django import forms
from django.utils.translation import ugettext_lazy as _

from leasing.enums import InvoiceState
from leasing.models import Invoice
from leasing.report.report_base import ReportBase


def get_lease_type(obj):
    return obj.lease.identifier.type.identifier


def get_lease_id(obj):
    return obj.lease.get_identifier_string()


class OpenInvoicesReport(ReportBase):
    name = _('Open invoices')
    description = _('Show all the invoices that have their state as "open"')
    slug = 'open_invoices'
    input_fields = {
        'start_date': forms.DateField(label=_('Start date'), required=True),
        'end_date': forms.DateField(label=_('End date'), required=True),
    }
    output_fields = {
        'number': {
            'label': _('Number'),
        },
        'lease_type': {
            'source': get_lease_type,
            'label': _('Lease type'),
        },
        'lease_id': {
            'source': get_lease_id,
            'label': _('Lease id'),
        },
        'due_date': {
            'label': _('Due date'),
            'format': 'date',
        },
        'total_amount': {
            'label': _('Total amount'),
            'format': 'money',
        },
        'billed_amount': {
            'label': _('Billed amount'),
            'format': 'money',
        },
        'outstanding_amount': {
            'label': _('Outstanding amount'),
            'format': 'money',
        },
    }

    def get_data(self, input_data):
        return Invoice.objects.filter(
            due_date__gte=input_data['start_date'],
            due_date__lte=input_data['end_date'],
            state=InvoiceState.OPEN
        ).select_related(
            'lease', 'lease__identifier', 'lease__identifier__type', 'lease__identifier__district',
            'lease__identifier__municipality',
        ).order_by('lease__identifier__type__identifier', 'due_date')
