from rest_framework import viewsets

from landuse.models.agreement import AuthorizedSignatory, DetailedPlan, District
from landuse.models.compensation import LandPolicyProgram
from landuse.models.site import SiteIntendedUse, SiteTenureType
from landuse.serializers.agreement import (
    AuthorizedSignatorySerializer,
    DetailedPlanSerializer,
    DistrictSerializer,
    LandPolicyProgramSerializer,
    SiteIntendedUseSerializer,
    SiteTenureTypeSerializer,
)
from landuse.views.mixins import LandUseApiEnabledFlagMixin


class LandUseLookupViewSet(LandUseApiEnabledFlagMixin, viewsets.ReadOnlyModelViewSet):
    pagination_class = None


class DistrictViewSet(LandUseLookupViewSet):
    queryset = District.objects.order_by("identifier", "pk")
    serializer_class = DistrictSerializer
    filterset_fields = ("identifier", "name")


class AuthorizedSignatoryViewSet(LandUseLookupViewSet):
    queryset = AuthorizedSignatory.objects.order_by("name", "pk")
    serializer_class = AuthorizedSignatorySerializer
    filterset_fields = ("name",)


class DetailedPlanViewSet(LandUseLookupViewSet):
    queryset = DetailedPlan.objects.order_by("plan_number", "pk")
    serializer_class = DetailedPlanSerializer
    filterset_fields = ("plan_number", "processing_stage")


class LandPolicyProgramViewSet(LandUseLookupViewSet):
    queryset = LandPolicyProgram.objects.order_by("name", "pk")
    serializer_class = LandPolicyProgramSerializer
    filterset_fields = ("name",)


class SiteIntendedUseViewSet(LandUseLookupViewSet):
    queryset = SiteIntendedUse.objects.order_by("name", "pk")
    serializer_class = SiteIntendedUseSerializer
    filterset_fields = ("name",)


class SiteTenureTypeViewSet(LandUseLookupViewSet):
    queryset = SiteTenureType.objects.order_by("name", "pk")
    serializer_class = SiteTenureTypeSerializer
    filterset_fields = ("name",)
