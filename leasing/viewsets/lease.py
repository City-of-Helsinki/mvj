import datetime

from dateutil import parser
from django.db.models import DurationField
from django.db.models.functions import Cast
from rest_framework.decorators import action
from rest_framework.exceptions import APIException
from rest_framework.response import Response

from leasing.filters import DistrictFilter, LeaseFilter
from leasing.models import (
    District, Financing, Hitas, IntendedUse, Lease, LeaseType, Management, Municipality, NoticePeriod, Regulation,
    RelatedLease, StatisticalUse, SupportiveHousing)
from leasing.models.utils import get_billing_periods_for_year
from leasing.serializers.explanation import ExplanationSerializer
from leasing.serializers.invoice import CreateChargeSerializer
from leasing.serializers.lease import (
    DistrictSerializer, FinancingSerializer, HitasSerializer, IntendedUseSerializer, LeaseCreateUpdateSerializer,
    LeaseListSerializer, LeaseRetrieveSerializer, LeaseSuccinctSerializer, LeaseTypeSerializer, ManagementSerializer,
    MunicipalitySerializer, NoticePeriodSerializer, RegulationSerializer, RelatedLeaseSerializer,
    StatisticalUseSerializer, SupportiveHousingSerializer)

from .utils import AtomicTransactionModelViewSet, AuditLogMixin


class DistrictViewSet(AtomicTransactionModelViewSet):
    queryset = District.objects.all()
    serializer_class = DistrictSerializer
    filterset_class = DistrictFilter


class FinancingViewSet(AtomicTransactionModelViewSet):
    queryset = Financing.objects.all()
    serializer_class = FinancingSerializer


class HitasViewSet(AtomicTransactionModelViewSet):
    queryset = Hitas.objects.all()
    serializer_class = HitasSerializer


class IntendedUseViewSet(AtomicTransactionModelViewSet):
    queryset = IntendedUse.objects.all()
    serializer_class = IntendedUseSerializer


class LeaseTypeViewSet(AtomicTransactionModelViewSet):
    queryset = LeaseType.objects.all()
    serializer_class = LeaseTypeSerializer


class ManagementViewSet(AtomicTransactionModelViewSet):
    queryset = Management.objects.all()
    serializer_class = ManagementSerializer


class MunicipalityViewSet(AtomicTransactionModelViewSet):
    queryset = Municipality.objects.all()
    serializer_class = MunicipalitySerializer


class NoticePeriodViewSet(AtomicTransactionModelViewSet):
    queryset = NoticePeriod.objects.all().annotate(duration_as_interval=Cast('duration', DurationField())).order_by(
        'duration_as_interval')
    serializer_class = NoticePeriodSerializer


class RegulationViewSet(AtomicTransactionModelViewSet):
    queryset = Regulation.objects.all()
    serializer_class = RegulationSerializer


class StatisticalUseViewSet(AtomicTransactionModelViewSet):
    queryset = StatisticalUse.objects.all()
    serializer_class = StatisticalUseSerializer


class SupportiveHousingViewSet(AtomicTransactionModelViewSet):
    queryset = SupportiveHousing.objects.all()
    serializer_class = SupportiveHousingSerializer


class RelatedLeaseViewSet(AtomicTransactionModelViewSet):
    queryset = RelatedLease.objects.all()
    serializer_class = RelatedLeaseSerializer


class LeaseViewSet(AuditLogMixin, AtomicTransactionModelViewSet):
    serializer_class = LeaseRetrieveSerializer
    filterset_class = LeaseFilter

    def get_queryset(self):
        """Allow filtering leases by lease identifier

        `identifier` query parameter can be used to find the Lease with the provided identifier.
        example: .../lease/?identifier=S0120-219
        """
        identifier = self.request.query_params.get('identifier')
        succinct = self.request.query_params.get('succinct')

        if succinct:
            queryset = Lease.objects.succinct_select_related_and_prefetch_related()
        else:
            queryset = Lease.objects.full_select_related_and_prefetch_related()

        if identifier is not None:
            if len(identifier) < 3:
                queryset = queryset.filter(identifier__type__identifier__istartswith=identifier)
            elif len(identifier) == 3:
                queryset = queryset.filter(identifier__type__identifier__iexact=identifier[:2],
                                           identifier__municipality__identifier=identifier[2:3])
            elif len(identifier) < 7:
                district_identifier = identifier[3:5]
                if district_identifier == '0':
                    queryset = queryset.filter(identifier__type__identifier__iexact=identifier[:2],
                                               identifier__municipality__identifier=identifier[2:3],
                                               identifier__district__identifier__in=range(0, 10))
                else:
                    if district_identifier != '00':
                        district_identifier = district_identifier.lstrip('0')

                    queryset = queryset.filter(identifier__type__identifier__iexact=identifier[:2],
                                               identifier__municipality__identifier=identifier[2:3],
                                               identifier__district__identifier__startswith=district_identifier)
            else:
                queryset = queryset.filter(identifier__type__identifier__iexact=identifier[:2],
                                           identifier__municipality__identifier=identifier[2:3],
                                           identifier__district__identifier=identifier[3:5],
                                           identifier__sequence__startswith=identifier[6:])

        return queryset

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update', 'metadata'):
            return LeaseCreateUpdateSerializer

        if self.request.query_params.get('succinct'):
            return LeaseSuccinctSerializer

        if self.action == 'list':
            return LeaseListSerializer

        return LeaseRetrieveSerializer

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

    @action(methods=['post'], detail=True)
    def create_charge(self, request, pk=None):
        lease = self.get_object()
        request.data['lease'] = lease

        serializer = CreateChargeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=201)
