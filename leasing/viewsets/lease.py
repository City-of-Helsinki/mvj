import datetime
import re

from dateutil import parser
from django.db.models import DurationField
from django.db.models.functions import Cast
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import APIException
from rest_framework.response import Response

from leasing.filters import DistrictFilter, LeaseFilter
from leasing.models import (
    District, Financing, Hitas, IntendedUse, Lease, LeaseType, Management, Municipality, NoticePeriod, Regulation,
    StatisticalUse, SupportiveHousing)
from leasing.models.utils import get_billing_periods_for_year
from leasing.serializers.explanation import ExplanationSerializer
from leasing.serializers.lease import (
    DistrictSerializer, FinancingSerializer, HitasSerializer, IntendedUseSerializer, LeaseCreateUpdateSerializer,
    LeaseSerializer, LeaseTypeSerializer, ManagementSerializer, MunicipalitySerializer, NoticePeriodSerializer,
    RegulationSerializer, StatisticalUseSerializer, SupportiveHousingSerializer)
from leasing.viewsets.utils import AuditLogMixin


class DistrictViewSet(viewsets.ModelViewSet):
    queryset = District.objects.all()
    serializer_class = DistrictSerializer
    filter_class = DistrictFilter


class FinancingViewSet(viewsets.ModelViewSet):
    queryset = Financing.objects.all()
    serializer_class = FinancingSerializer


class HitasViewSet(viewsets.ModelViewSet):
    queryset = Hitas.objects.all()
    serializer_class = HitasSerializer


class IntendedUseViewSet(viewsets.ModelViewSet):
    queryset = IntendedUse.objects.all()
    serializer_class = IntendedUseSerializer


class LeaseTypeViewSet(viewsets.ModelViewSet):
    queryset = LeaseType.objects.all()
    serializer_class = LeaseTypeSerializer


class ManagementViewSet(viewsets.ModelViewSet):
    queryset = Management.objects.all()
    serializer_class = ManagementSerializer


class MunicipalityViewSet(viewsets.ModelViewSet):
    queryset = Municipality.objects.all()
    serializer_class = MunicipalitySerializer


class NoticePeriodViewSet(viewsets.ModelViewSet):
    queryset = NoticePeriod.objects.all().annotate(duration_as_interval=Cast('duration', DurationField())).order_by(
        'duration_as_interval')
    serializer_class = NoticePeriodSerializer


class RegulationViewSet(viewsets.ModelViewSet):
    queryset = Regulation.objects.all()
    serializer_class = RegulationSerializer


class StatisticalUseViewSet(viewsets.ModelViewSet):
    queryset = StatisticalUse.objects.all()
    serializer_class = StatisticalUseSerializer


class SupportiveHousingViewSet(viewsets.ModelViewSet):
    queryset = SupportiveHousing.objects.all()
    serializer_class = SupportiveHousingSerializer


class LeaseViewSet(AuditLogMixin, viewsets.ModelViewSet):
    queryset = Lease.objects.all().select_related(
        'type', 'municipality', 'district', 'identifier', 'identifier__type', 'identifier__municipality',
        'identifier__district', 'lessor', 'intended_use', 'supportive_housing', 'statistical_use', 'financing',
        'management', 'regulation', 'hitas', 'notice_period', 'preparer'
    ).prefetch_related(
        'related_leases', 'tenants', 'tenants__tenantcontact_set', 'tenants__tenantcontact_set__contact',
        'lease_areas', 'contracts', 'decisions', 'inspections', 'rents', 'rents__due_dates', 'rents__contract_rents',
        'rents__contract_rents__intended_use', 'rents__rent_adjustments', 'rents__rent_adjustments__intended_use',
        'rents__index_adjusted_rents', 'rents__payable_rents', 'rents__fixed_initial_year_rents',
        'rents__fixed_initial_year_rents__intended_use', 'lease_areas__addresses', 'basis_of_rents'
    )
    serializer_class = LeaseSerializer
    filter_class = LeaseFilter

    def get_queryset(self):
        """Allow filtering leases by lease identifier

        `identifier` query parameter can be used to find the Lease with the provided identifier.
        example: .../lease/?identifier=S0120-219
        """
        queryset = super().get_queryset()

        identifier = self.request.query_params.get('identifier', None)

        if identifier is not None:
            id_match = re.match(r'(?P<lease_type>\w\d)(?P<municipality>\d)(?P<district>\d{2})-(?P<sequence>\d+)$',
                                identifier)

            if id_match:
                queryset = queryset.filter(identifier__type__identifier=id_match.group('lease_type'),
                                           identifier__municipality__identifier=id_match.group('municipality'),
                                           identifier__district__identifier=id_match.group('district'),
                                           identifier__sequence=id_match.group('sequence'))

        return queryset

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update', 'metadata'):
            return LeaseCreateUpdateSerializer

        return LeaseSerializer

    def create(self, request, *args, **kwargs):
        if 'preparer' not in request.data:
            request.data['preparer'] = request.user.id

        return super().create(request, *args, **kwargs)

    @action(methods=['get'], detail=True)
    def rent_for_period(self, request, pk=None):
        lease = self.get_object()

        if 'start_date' not in request.query_params or 'end_date' not in request.query_params:
            raise APIException('Both start_date and end_data parameters are mandatory')

        start_date = parser.parse(request.query_params['start_date']).date()
        end_date = parser.parse(request.query_params['end_date']).date()

        result = {
            'start_date': start_date,
            'end_date': end_date,
            'rents': [],
        }

        for rent in lease.rents.all():
            (rent_amount, explanation) = rent.get_amount_for_date_range(start_date, end_date, explain=True)

            explanation_serializer = ExplanationSerializer(explanation)

            result['rents'].append({
                'id': rent.id,
                'start_date': rent.start_date,
                'end_date': rent.end_date,
                'amount': rent_amount,
                'explanation': explanation_serializer.data,
            })

        return Response(result)

    @action(methods=['get'], detail=True)
    def billing_periods(self, request, pk=None):
        lease = self.get_object()

        if 'year' in request.query_params:
            year = int(request.query_params['year'])
        else:
            year = datetime.date.today().year

        start_date = datetime.date(year=year, month=1, day=1)
        end_date = datetime.date(year=year, month=12, day=31)

        billing_periods = []
        for rent in lease.rents.all():
            due_dates_per_year = rent.get_due_dates_for_period(start_date, end_date)
            billing_periods.extend(get_billing_periods_for_year(year, len(due_dates_per_year)))

        return Response({
            'billing_periods': billing_periods
        })
