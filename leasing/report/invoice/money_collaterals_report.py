from django import forms
from django.utils.translation import ugettext_lazy as _

from leasing.models import Collateral
from leasing.report.report_base import ReportBase


def get_lease_id(obj):
    return obj.contract.lease.get_identifier_string()


class MoneyCollateralsReport(ReportBase):
    name = _('Money collaterals')
    description = _('Show all money collaterals')
    slug = 'money_collaterals'
    input_fields = {
        'paid': forms.NullBooleanField(label=_('Paid'), required=False),
        'returned': forms.NullBooleanField(label=_('Returned'), required=False),
    }
    output_fields = {
        'lease_id': {
            'source': get_lease_id,
            'label': _('Lease id'),
        },
        'total_amount': {
            'label': _('Total amount'),
            'format': 'money',
            'width': 13,
        },
        'paid_date': {
            'label': _('Paid date'),
            'format': 'date',
        },
        'returned_date': {
            'label': _('Returned date'),
            'format': 'date',
        },
        'note': {
            'label': _('Note'),
            'width': 50,
        },
    }

    def get_data(self, input_data):
        qs = Collateral.objects.all().select_related(
            'contract',
            'contract__lease', 'contract__lease__identifier', 'contract__lease__identifier__type',
            'contract__lease__identifier__district', 'contract__lease__identifier__municipality'
        ).order_by(
            'contract__lease__identifier__type__identifier',
            'contract__lease__identifier__municipality__identifier',
            'contract__lease__identifier__district__identifier',
            'contract__lease__identifier__sequence',
        )

        if input_data['paid'] is not None:
            qs = qs.filter(paid_date__isnull=not input_data['paid'])

        if input_data['returned'] is not None:
            qs = qs.filter(returned_date__isnull=not input_data['returned'])

        return qs
