import datetime

from django.db.models import DurationField, Q
from django.db.models.functions import Cast
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter

from field_permissions.viewsets import FieldPermissionsViewsetMixin
from leasing.filters import DistrictFilter, LeaseFilter
from leasing.forms import LeaseSearchForm
from leasing.models import (
    District, Financing, Hitas, IntendedUse, Lease, LeaseType, Management, Municipality, NoticePeriod, Regulation,
    RelatedLease, SpecialProject, StatisticalUse, SupportiveHousing)
from leasing.serializers.lease import (
    DistrictSerializer, FinancingSerializer, HitasSerializer, IntendedUseSerializer, LeaseCreateSerializer,
    LeaseListSerializer, LeaseRetrieveSerializer, LeaseSuccinctSerializer, LeaseTypeSerializer, LeaseUpdateSerializer,
    ManagementSerializer, MunicipalitySerializer, NoticePeriodSerializer, RegulationSerializer, RelatedLeaseSerializer,
    SpecialProjectSerializer, StatisticalUseSerializer, SupportiveHousingSerializer)

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


class SpecialProjectViewSet(AtomicTransactionModelViewSet):
    queryset = SpecialProject.objects.all()
    serializer_class = SpecialProjectSerializer


class RelatedLeaseViewSet(AtomicTransactionModelViewSet):
    queryset = RelatedLease.objects.all()
    serializer_class = RelatedLeaseSerializer


class LeaseViewSet(AuditLogMixin, FieldPermissionsViewsetMixin, AtomicTransactionModelViewSet):
    serializer_class = LeaseRetrieveSerializer
    filterset_class = LeaseFilter
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    ordering = (
        'identifier__type__identifier', 'identifier__municipality__identifier', 'identifier__district__identifier',
        'identifier__sequence'
    )
    ordering_fields = (
        'identifier__type__identifier', 'identifier__municipality__identifier', 'identifier__district__identifier',
        'identifier__sequence', 'lessor__name', 'state', 'start_date', 'end_date'
    )

    def get_queryset(self):  # noqa: C901
        """Allow filtering leases by various query parameters

        `identifier` query parameter can be used to find the Lease with the provided identifier.
        example: .../lease/?identifier=S0120-219
        """
        identifier = self.request.query_params.get('identifier')
        succinct = self.request.query_params.get('succinct')

        if succinct:
            queryset = Lease.objects.succinct_select_related_and_prefetch_related()
        else:
            queryset = Lease.objects.full_select_related_and_prefetch_related()

        if self.action != 'list':
            return queryset

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
                district_identifier = identifier[3:5]
                if district_identifier == "00":
                    district_identifier = '0'
                else:
                    district_identifier = district_identifier.lstrip('0')

                queryset = queryset.filter(identifier__type__identifier__iexact=identifier[:2],
                                           identifier__municipality__identifier=identifier[2:3],
                                           identifier__district__identifier=district_identifier,
                                           identifier__sequence__startswith=identifier[6:])

        search_form = LeaseSearchForm(self.request.query_params)

        if search_form.is_valid():
            if search_form.cleaned_data.get('tenant_name'):
                tenant_name = search_form.cleaned_data.get('tenant_name')
                queryset = queryset.filter(
                    Q(tenants__tenantcontact__contact__name__icontains=tenant_name) |
                    Q(tenants__tenantcontact__contact__first_name__icontains=tenant_name) |
                    Q(tenants__tenantcontact__contact__last_name__icontains=tenant_name)
                )

                # Limit further only if searching by tenants
                if search_form.cleaned_data.get('tenantcontact_type'):
                    queryset = queryset.filter(tenants__tenantcontact__type__in=search_form.cleaned_data.get(
                        'tenantcontact_type'))

                if search_form.cleaned_data.get('only_past_tenants'):
                    queryset = queryset.filter(tenants__tenantcontact__end_date__lte=datetime.date.today())

            if search_form.cleaned_data.get('sequence'):
                queryset = queryset.filter(identifier__sequence=search_form.cleaned_data.get('sequence'))

            if search_form.cleaned_data.get('lease_start_date_start'):
                queryset = queryset.filter(start_date__gte=search_form.cleaned_data.get('lease_start_date_start'))

            if search_form.cleaned_data.get('lease_start_date_end'):
                queryset = queryset.filter(start_date__lte=search_form.cleaned_data.get('lease_start_date_end'))

            if search_form.cleaned_data.get('lease_end_date_start'):
                queryset = queryset.filter(end_date__gte=search_form.cleaned_data.get('lease_end_date_start'))

            if search_form.cleaned_data.get('lease_end_date_end'):
                queryset = queryset.filter(end_date__lte=search_form.cleaned_data.get('lease_end_date_end'))

            if search_form.cleaned_data.get('only_active_leases'):
                queryset = queryset.filter(
                    (Q(start_date__isnull=True) | Q(start_date__lte=datetime.date.today())) &
                    (Q(end_date__isnull=True) | Q(end_date__gte=datetime.date.today()))
                )

            if search_form.cleaned_data.get('only_expired_leases'):
                queryset = queryset.filter(end_date__lte=datetime.date.today())

            if search_form.cleaned_data.get('property_identifier'):
                queryset = queryset.filter(
                    lease_areas__identifier__icontains=search_form.cleaned_data.get('property_identifier'))

            if search_form.cleaned_data.get('address'):
                queryset = queryset.filter(
                    lease_areas__addresses__address__icontains=search_form.cleaned_data.get('address'))

            if search_form.cleaned_data.get('lease_state'):
                queryset = queryset.filter(state__in=search_form.cleaned_data.get('lease_state'))

            if search_form.cleaned_data.get('business_id'):
                queryset = queryset.filter(
                    tenants__tenantcontact__contact__business_id__icontains=search_form.cleaned_data.get('business_id'))

            if search_form.cleaned_data.get('national_identification_number'):
                nat_id = search_form.cleaned_data.get('national_identification_number')
                queryset = queryset.filter(
                    tenants__tenantcontact__contact__national_identification_number__icontains=nat_id)

            if search_form.cleaned_data.get('lessor'):
                queryset = queryset.filter(lessor=search_form.cleaned_data.get('lessor'))

            if search_form.cleaned_data.get('contract_number'):
                queryset = queryset.filter(contracts__contract_number__icontains=search_form.cleaned_data.get(
                    'contract_number'))

            if search_form.cleaned_data.get('decision_maker'):
                queryset = queryset.filter(decisions__decision_maker=search_form.cleaned_data.get(
                    'decision_maker'))

            if search_form.cleaned_data.get('decision_date'):
                queryset = queryset.filter(decisions__decision_date=search_form.cleaned_data.get(
                    'decision_date'))

            if search_form.cleaned_data.get('decision_section'):
                queryset = queryset.filter(decisions__section=search_form.cleaned_data.get(
                    'decision_section'))

            if search_form.cleaned_data.get('reference_number'):
                reference_number = search_form.cleaned_data.get('reference_number')
                queryset = queryset.filter(Q(reference_number__icontains=reference_number) | Q(
                    decisions__reference_number__icontains=reference_number))

            if search_form.cleaned_data.get('invoice_number'):
                queryset = queryset.filter(
                    invoices__number__icontains=search_form.cleaned_data.get('invoice_number'))

        return queryset.distinct()

    def get_serializer_class(self):
        if self.action in ('create', 'metadata'):
            return LeaseCreateSerializer

        if self.action in ('update', 'partial_update'):
            return LeaseUpdateSerializer

        if self.request.query_params.get('succinct'):
            return LeaseSuccinctSerializer

        if self.action == 'list':
            return LeaseListSerializer

        return LeaseRetrieveSerializer

    def perform_create(self, serializer):
        relate_to = None
        if 'relate_to' in serializer.validated_data:
            relate_to = serializer.validated_data.pop('relate_to')

        relation_type = None
        if 'relation_type' in serializer.validated_data:
            relation_type = serializer.validated_data.pop('relation_type')

        instance = serializer.save()

        if relate_to and relation_type:
            RelatedLease.objects.create(from_lease=relate_to, to_lease=instance, type=relation_type)

    def create(self, request, *args, **kwargs):
        if 'preparer' not in request.data:
            request.data['preparer'] = request.user.id

        return super().create(request, *args, **kwargs)
