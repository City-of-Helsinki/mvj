from rest_framework import viewsets

from leasing.filters import LeaseFilter
from leasing.models import (
    District, Financing, Hitas, IntendedUse, Lease, LeaseType, Management, Municipality, NoticePeriod, Regulation,
    StatisticalUse, SupportiveHousing)
from leasing.serializers.lease import (
    DistrictSerializer, FinancingSerializer, HitasSerializer, IntendedUseSerializer, LeaseCreateUpdateSerializer,
    LeaseSerializer, LeaseTypeSerializer, ManagementSerializer, MunicipalitySerializer, NoticePeriodSerializer,
    RegulationSerializer, StatisticalUseSerializer, SupportiveHousingSerializer)
from leasing.viewsets.utils import AuditLogMixin


class DistrictViewSet(viewsets.ModelViewSet):
    queryset = District.objects.all()
    serializer_class = DistrictSerializer


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
    queryset = NoticePeriod.objects.all()
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
    queryset = Lease.objects.all().select_related('type', 'municipality', 'district', 'identifier', 'lessor',
                                                  'intended_use', 'supportive_housing', 'statistical_use', 'financing',
                                                  'management', 'regulation', 'hitas', 'notice_period')
    serializer_class = LeaseSerializer
    filter_class = LeaseFilter

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return LeaseCreateUpdateSerializer

        return LeaseSerializer
