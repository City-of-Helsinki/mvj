import datetime

from dateutil.parser import parse, parserinfo
from django.db.models import DurationField, Q
from django.db.models.functions import Cast
from django.utils.translation import ugettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response

from field_permissions.viewsets import FieldPermissionsViewsetMixin
from leasing.filters import DistrictFilter, LeaseFilter
from leasing.forms import LeaseSearchForm
from leasing.models import (
    District, Financing, Hitas, IntendedUse, Lease, LeaseType, Management, Municipality, NoticePeriod, Regulation,
    RelatedLease, SpecialProject, StatisticalUse, SupportiveHousing)
from leasing.models.utils import normalize_property_identifier
from leasing.serializers.common import ManagementSerializer
from leasing.serializers.lease import (
    DistrictSerializer, FinancingSerializer, HitasSerializer, IntendedUseSerializer, LeaseCreateSerializer,
    LeaseListSerializer, LeaseRetrieveSerializer, LeaseSuccinctSerializer, LeaseTypeSerializer, LeaseUpdateSerializer,
    MunicipalitySerializer, NoticePeriodSerializer, RegulationSerializer, RelatedLeaseSerializer,
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

        # Simple search
        if identifier is not None:
            # Search by identifier or parts of it
            if len(identifier) < 3:
                identifier_q = Q(identifier__type__identifier__istartswith=identifier)
            elif len(identifier) == 3:
                identifier_q = Q(identifier__type__identifier__iexact=identifier[:2],
                                 identifier__municipality__identifier=identifier[2:3])
            elif len(identifier) < 7:
                district_identifier = identifier[3:5]
                if district_identifier == '0':
                    identifier_q = Q(identifier__type__identifier__iexact=identifier[:2],
                                     identifier__municipality__identifier=identifier[2:3],
                                     identifier__district__identifier__in=range(0, 10))
                else:
                    if district_identifier != '00':
                        district_identifier = district_identifier.lstrip('0')

                    identifier_q = Q(identifier__type__identifier__iexact=identifier[:2],
                                     identifier__municipality__identifier=identifier[2:3],
                                     identifier__district__identifier__startswith=district_identifier)
            else:
                district_identifier = identifier[3:5]
                if district_identifier == "00":
                    district_identifier = '0'
                else:
                    district_identifier = district_identifier.lstrip('0')

                identifier_q = Q(identifier__type__identifier__iexact=identifier[:2],
                                 identifier__municipality__identifier=identifier[2:3],
                                 identifier__district__identifier=district_identifier,
                                 identifier__sequence__startswith=identifier[6:])

            # Search from other fields
            other_q = Q()

            # Address
            other_q |= Q(lease_areas__addresses__address__icontains=identifier)

            # Property identifier
            other_q |= Q(lease_areas__identifier__icontains=identifier)
            normalized_identifier = normalize_property_identifier(identifier)
            other_q |= Q(lease_areas__identifier__icontains=normalized_identifier)

            # Tenantcontact name
            other_q |= Q(tenants__tenantcontact__contact__name__icontains=identifier)
            other_q |= Q(tenants__tenantcontact__contact__first_name__icontains=identifier)
            other_q |= Q(tenants__tenantcontact__contact__last_name__icontains=identifier)

            # Lessor
            other_q |= Q(lessor__name__icontains=identifier)
            other_q |= Q(lessor__first_name__icontains=identifier)
            other_q |= Q(lessor__last_name__icontains=identifier)

            # Date
            try:
                search_date = parse(identifier, parserinfo=parserinfo(dayfirst=True))
                if search_date:
                    other_q |= Q(start_date=search_date.date())
                    other_q |= Q(end_date=search_date.date())
            except ValueError:
                pass

            queryset = queryset.filter(identifier_q | other_q)

        # Advanced search
        search_form = LeaseSearchForm(self.request.query_params)

        if search_form.is_valid():
            if search_form.cleaned_data.get('tenant_name'):
                tenant_name = search_form.cleaned_data.get('tenant_name')

                q = Q(
                    Q(tenants__tenantcontact__contact__name__icontains=tenant_name) |
                    Q(tenants__tenantcontact__contact__first_name__icontains=tenant_name) |
                    Q(tenants__tenantcontact__contact__last_name__icontains=tenant_name)
                )

                if search_form.cleaned_data.get('tenantcontact_type'):
                    q &= Q(tenants__tenantcontact__type__in=search_form.cleaned_data.get(
                        'tenantcontact_type'))

                if search_form.cleaned_data.get('only_past_tenants'):
                    q &= Q(tenants__tenantcontact__end_date__lte=datetime.date.today())

                queryset = queryset.filter(q)

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

            # Filter by active / expired only when only one of the options is set
            if bool(search_form.cleaned_data.get('only_active_leases')) ^ bool(
                    search_form.cleaned_data.get('only_expired_leases')):
                if search_form.cleaned_data.get('only_active_leases'):
                    # No need to filter by start date because future start dates are also considered active
                    queryset = queryset.filter(Q(end_date__isnull=True) | Q(end_date__gte=datetime.date.today()))

                if search_form.cleaned_data.get('only_expired_leases'):
                    queryset = queryset.filter(end_date__lte=datetime.date.today())

            if 'has_geometry' in search_form.cleaned_data:
                if search_form.cleaned_data.get('has_geometry') is True:
                    queryset = queryset.filter(lease_areas__geometry__isnull=False)

                if search_form.cleaned_data.get('has_geometry') is False:
                    queryset = queryset.filter(lease_areas__geometry__isnull=True)

            if search_form.cleaned_data.get('property_identifier'):
                property_identifier = search_form.cleaned_data.get('property_identifier')
                normalized_identifier = normalize_property_identifier(property_identifier)

                queryset = queryset.filter(
                    Q(lease_areas__identifier__icontains=property_identifier) | Q(
                        lease_areas__identifier__icontains=normalized_identifier)
                )

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

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        if (instance.preparer == request.user and instance.is_empty()) or request.user.has_perm(
                'leasing.delete_nonempty_lease'):
            self.perform_destroy(instance)

            return Response(status=status.HTTP_204_NO_CONTENT)

        raise PermissionDenied(_("No permission. Can only delete own empty leases."))
