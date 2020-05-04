import datetime

from django import forms
from django.db.models import Avg, Q, Sum
from django.utils.translation import ugettext_lazy as _
from rest_framework.response import Response

from leasing.enums import LeaseAreaAttachmentType, LeaseState, SubventionType
from leasing.models import Lease
from leasing.report.report_base import ReportBase

LIVING = [1, 12, 13]  # TODO: Can we get rid of static ids


def get_type(obj):
    if(not obj.state):
        return
    return obj.state.value


def get_lease_id(obj):
    return obj.get_identifier_string()


def get_tenants(obj):
    now = datetime.date.today()
    return ', '.join([c.get_name() for c in obj.get_tenant_shares_for_period(now, now)]),


def get_address(obj):
    addresses = []

    for lease_area in obj.lease_areas.all():
        if lease_area.archived_at:
            continue

        addresses.extend([la.address for la in lease_area.addresses.filter(is_primary=True)])

    return ' / '.join(addresses)


def get_plan_units(obj):
    return
    plan_units = []

    for lease_area in obj.lease_areas.all():
        if lease_area.archived_at:
            continue

        plan_units.extend(lease_area.plan_unit)

    return ' / '.join(plan_units)


def get_supportive_housing(obj):
    if(not obj.supportive_housing):
        return
    return obj.supportive_housing.name


def get_notice_period(obj):
    if(not obj.notice_period):
        return
    return obj.notice_period.name


def get_district(obj):
    if(not obj.district):
        return
    return '{} {}'.format(obj.district.identifier, obj.district.name)


def get_preparer(obj):
    if(not obj.preparer):
        return
    return '{} {}'.format(obj.preparer.last_name, obj.preparer.first_name)


def get_form_of_management(obj):
    if(not obj.management):
        return
    return obj.management.name


def get_lessor(obj):
    if(not obj.lessor):
        return
    return obj.lessor.name


def get_form_of_regulation(obj):
    if(not obj.regulation):
        return
    return obj.regulation.name


def get_contract_number(obj):
    contract_numbers = []
    for contract in obj.contracts.filter(contract_number__isnull=False).exclude(contract_number=''):
        contract_numbers.append(contract.contract_number)
    return ' / '.join(contract_numbers)


def get_matti_report(obj):
    for lease_area in obj.lease_areas.all():
        if lease_area.archived_at:
            continue
        if(lease_area.attachments.filter(type=LeaseAreaAttachmentType.MATTI_REPORT)):
            return True
    return False


def get_buy_right(obj):
    for decisions in obj.decisions.all():
        if(decisions.conditions.filter(type_id=24)):  # TODO: Can we get rid of static type_id
            return True
    return False


def get_lease_area_identifier(obj):
    lease_area_identifiers = []

    for lease_area in obj.lease_areas.all():
        if lease_area.archived_at:
            continue

        lease_area_identifiers.extend([lease_area.identifier])

    return ' / '.join(lease_area_identifiers)


def get_total_rent_amount_for_year(obj):
    year = datetime.date.today().year
    return obj.calculate_rent_amount_for_year(year).get_total_amount()


def get_total_area(obj):
    return obj.lease_areas.aggregate(Sum('area'))['area__sum']


def get_re_lease(obj):
    year = datetime.date.today().year
    year_start = datetime.date(year, 1, 1)
    year_end = datetime.date(year, 12, 31)
    for rent in obj.get_active_rents_on_period(year_start, year_end):
        if(rent.rent_adjustments.filter(subvention_type=SubventionType.RE_LEASE)):
            return True
    return False


def get_build_permission_living(obj):
    qs = obj.basis_of_rents.filter(intended_use__id__in=LIVING).values('area_unit').annotate(area=Sum('area'))
    return ' / '.join(['{} {}'.format(i.get('area'), i.get('area_unit')) for i in qs])


def get_build_permission_business(obj):
    qs = obj.basis_of_rents.exclude(intended_use__id__in=LIVING).values('area_unit').annotate(area=Sum('area'))
    return ' / '.join(['{} {}'.format(i.get('area'), i.get('area_unit')) for i in qs])


def get_build_permission_total(obj):
    qs = obj.basis_of_rents.all().values('area_unit').annotate(area=Sum('area'))
    return ' / '.join(['{} {}'.format(i.get('area'), i.get('area_unit')) for i in qs])


def get_rent_amount_living(obj):
    year = datetime.date.today().year
    sum = 0
    for a in obj.calculate_rent_amount_for_year(year).amounts:
        for tabiu, value in a.get_total_amounts_by_intended_uses().items():
            if(tabiu.id in LIVING):
                sum += value
    return sum


def get_rent_amount_business(obj):
    year = datetime.date.today().year
    sum = 0
    for a in obj.calculate_rent_amount_for_year(year).amounts:
        for tabiu, value in a.get_total_amounts_by_intended_uses().items():
            if(tabiu.id not in LIVING):
                sum += value
    return sum


def get_rent_amount_for_year(obj):
    year = datetime.date.today().year
    return obj.calculate_rent_amount_for_year(year).get_total_amount()


def get_floor_m2_living(obj):
    qs = obj.basis_of_rents.filter(intended_use__id__in=LIVING).values(
        'area_unit').annotate(amount_per_area=Avg('amount_per_area'))
    return ' / '.join(['{} {}'.format(i.get('amount_per_area'), i.get('area_unit')) for i in qs])


def get_floor_m2_business(obj):
    qs = obj.basis_of_rents.exclude(intended_use__id__in=LIVING).values(
        'area_unit').annotate(amount_per_area=Avg('amount_per_area'))
    return ' / '.join(['{} {}'.format(i.get('amount_per_area'), i.get('area_unit')) for i in qs])


class LeaseStatisticReport(ReportBase):
    name = _('Lease Statistic')
    description = _('Lease statistics')
    slug = 'lease_statistic'
    input_fields = {
        'start_date': forms.DateField(label=_('Start date'), required=True),
        'end_date': forms.DateField(label=_('End date'), required=True),
        'state': forms.ChoiceField(label=_('State'), required=False, choices=LeaseState.choices()),
        'only_active_leases': forms.BooleanField(label=_('State'), required=False)

    }
    output_fields = {
        'lease_id': {
            'label': _('Lease id'),
            'source': get_lease_id,
        },
        # Sopimusnumero
        'contract_number': {
            'label': _('Contract number'),
            'source': get_contract_number,
        },
        # Vuokrauksen tyyppi
        'type': {
            'label': _('Statistic report', 'Lease type'),
            'source': get_type
        },
        # Valmistelija
        'preparer': {
            'label': _('Preparer'),
            'source': get_preparer
        },
        # Kaupunginosa
        'district': {
            'label': _('District'),
            'source': get_district
        },
        # Kohteen tunnus
        'lease_area_identifier': {
            'label': _('Statistic report', 'Lease area identifier'),
            'source': get_lease_area_identifier
        },

        # Osoite
        'address': {
            'label': _('Address'),
            'source': get_address,
        },
        # Vuokranantaja
        'lessor': {
            'label': _("Lessor"),
            'source': get_lessor
        },
        # Rakennuttaja
        'real_estate_developer': {
            'label': _("Real estate developer"),
        },

        # Vuokralaiset
        'tenants': {
            'label': _('Model name', 'Tenants'),
            'source': get_tenants,
        },
        # Start date
        'start_date': {
            'label': _("Start date"),
        },
        # End date
        'end_date': {
            'label': _("End date"),
        },
        # Kokonaispinta-ala
        'total_area': {
            'label': _('Statistic report', 'Total area'),
            'source': get_total_area,
        },
        # Rakennus-oikeus-asuminen
        'build_permission_living': {
            'label': _('Statistic report', 'Build permission living'),
            'source': get_build_permission_living,
        },
        # Vuosivuokra Asuminen
        'rent_amount_living': {
            'label': _('Statistic report', 'Rent amount living'),
            'source': get_rent_amount_living,
        },
        # Rakennusoikeus Yritystila
        'build_permission_business': {
            'label': _('Statistic report', 'Build permission business'),
            'source': get_build_permission_business,
        },
        # Vuosivuokra Yritystila
        'rent_amount_business': {
            'label': _('Statistic report', 'Rent amount business'),
            'source': get_rent_amount_business,
        },
        # Kokonais rakennusoikeus
        'build_permission_total': {
            'label': _('Statistic report', 'Build permission total'),
            'source': get_build_permission_total,
        },
        # Vuosivuokra yhteensä
        'total_rent_amount_for_year': {
            'label': _('Statistic report', 'Rent amount for year'),
            'source': get_total_rent_amount_for_year,
        },
        # €/k-m2 Asuminen
        'floor_m2_living': {
            'label': _('Statistic report', 'Floor m2 living'),
            'source': get_floor_m2_living,
        },
        # €/k-m2 Yritystila
        'floor_m2_business': {
            'label': _('Statistic report', 'Floor m2 business'),
            'source': get_floor_m2_business,
        },
        # Kaavamerkintä
        'plan_units': {
            'label': _('Model name', 'Plan units'),
            'source': get_plan_units,
        },
        # Hallintamuoto
        'form_of_management': {
            'label': _('Model name', 'Form of management'),
            'source': get_form_of_management
        },
        # Eristysryhmä asunnot
        'supportive_housing': {
            'label': _('Supportive housing'),
            'source': get_supportive_housing
        },
        # Sääntelymuoto
        'form_of_regulation': {
            'label': _('Form of regulation'),
            'source': get_form_of_regulation
        },
        # Vuokraus uudelleen
        're_lease': {
            'label': _('Subvention type', 'Re-lease'),
            'source': get_re_lease
        },
        # Osto oikeus
        'buy_right': {
            'label': _('Statistic report', 'Buy right'),
            'source': get_buy_right
        },
        # Matti-raportti
        'matti_report': {
            'label': _('Lease area attachment type', 'Matti report'),
            'source': get_matti_report
        },
        # Irtisanomisaika
        'notice_period': {
            'label': _('Model name', 'Notice period'),
            'source': get_notice_period
        },
    }
    automatic_excel_column_labels = False

    def get_data(self, input_data):
        qs = Lease.objects.filter(
            (
                Q(start_date__gte=input_data['start_date']) &
                Q(start_date__lte=input_data['end_date'])
             ) | (
                Q(end_date__gte=input_data['start_date']) &
                Q(end_date__lte=input_data['end_date'])
            )
        ).select_related(
            'identifier__type',
            'identifier__district',
            'identifier__municipality',
            'lessor',
            'management',
            'district',
            'supportive_housing',
            'type',
            'notice_period',
        ).prefetch_related(
            'rents',
            'lease_areas',
            'lease_areas__addresses',
        )

        if input_data['state']:
            qs = qs.filter(state=input_data['state'])

        if input_data['only_active_leases']:
            qs = qs.filter(Q(end_date__isnull=True) | Q(end_date__gte=datetime.date.today()))

        return qs

    def get_response(self, request):
        report_data = self.get_data(self.get_input_data(request))
        serialized_report_data = self.serialize_data(report_data)

        return Response(serialized_report_data)
