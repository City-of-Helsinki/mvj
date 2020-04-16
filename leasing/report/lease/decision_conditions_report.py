from django import forms
from django.utils.translation import ugettext_lazy as _

from leasing.models import Condition
from leasing.report.report_base import ReportBase


def get_lease_id(obj):
    return obj.decision.lease.get_identifier_string()


def get_condition_type(obj):
    return obj.type.name


def get_area(obj):
    return ', '.join([la.identifier for la in obj.decision.lease.lease_areas.all() if la.archived_at is None])


def get_address(obj):
    addresses = []
    for lease_area in obj.decision.lease.lease_areas.all():
        if lease_area.archived_at:
            continue

        addresses.extend([la.address for la in lease_area.addresses.all()])

    return ' / '.join(addresses)


class DecisionConditionsReport(ReportBase):
    name = _('Decision conditions')
    description = _(
        'Show decision conditions that have their supervision date between the given dates. '
        'Excluding conditions that have a supervised date.'
    )
    slug = 'decision_conditions'
    input_fields = {
        'start_date': forms.DateField(label=_('Start date'), required=True),
        'end_date': forms.DateField(label=_('End date'), required=True),
    }
    output_fields = {
        'lease_id': {
            'source': get_lease_id,
            'label': _('Lease id'),
        },
        'area': {
            'source': get_area,
            'label': _('Lease area'),
            'width': 30,
        },
        'address': {
            'source': get_address,
            'label': _('Address'),
            'width': 50,
        },
        'type': {
            'source': get_condition_type,
            'label': _('Type'),
            'width': 25,
        },
        'supervision_date': {
            'label': _('Supervision date'),
            'format': 'date',
            'width': 15,
        },
        # Always empty due to filtering
        # 'supervised_date': {
        #     'label': _('Supervised date'),
        #     'format': 'date',
        # },
        'description': {
            'label': _('Description'),
            'width': 100,
        },
    }

    def get_data(self, input_data):
        qs = Condition.objects.filter(
            supervision_date__gte=input_data['start_date'],
            supervision_date__lte=input_data['end_date'],
            supervised_date__isnull=True
        ).select_related(
            'type',
            'decision',
            'decision__lease',
            'decision__lease__identifier',
            'decision__lease__identifier__type',
            'decision__lease__identifier__district',
            'decision__lease__identifier__municipality'
        ).prefetch_related(
            'decision__lease__lease_areas',
            'decision__lease__lease_areas__addresses',
        ).order_by(
            'supervision_date',
            'decision__lease__identifier__type__identifier',
            'decision__lease__identifier__municipality__identifier',
            'decision__lease__identifier__district__identifier',
            'decision__lease__identifier__sequence',
        )

        return qs
