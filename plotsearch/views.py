from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet
from rest_framework_gis.filters import InBBoxFilter

from field_permissions.viewsets import FieldPermissionsViewsetMixin
from leasing.permissions import MvjDjangoModelPermissionsOrAnonReadOnly
from leasing.viewsets.utils import AtomicTransactionModelViewSet, AuditLogMixin
from plotsearch.models import PlotSearch, PlotSearchSubtype, PlotSearchType
from plotsearch.serializers import (
    PlotSearchCreateSerializer,
    PlotSearchRetrieveSerializer,
    PlotSearchSubtypeSerializer,
    PlotSearchTypeSerializer,
    PlotSearchUpdateSerializer,
)


class PlotSearchSubtypeViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, GenericViewSet
):
    queryset = PlotSearchSubtype.objects.all()
    serializer_class = PlotSearchSubtypeSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_fields = ["plot_search_type"]


class PlotSearchTypeViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, GenericViewSet
):
    queryset = PlotSearchType.objects.all()
    serializer_class = PlotSearchTypeSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.prefetch_related("plotsearchsubtype_set")


class PlotSearchViewSet(
    AuditLogMixin, FieldPermissionsViewsetMixin, AtomicTransactionModelViewSet
):
    queryset = PlotSearch.objects.all()
    serializer_class = PlotSearchRetrieveSerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter, InBBoxFilter)
    permission_classes = (MvjDjangoModelPermissionsOrAnonReadOnly,)
    filterset_fields = ["search_class", "stage"]

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.prefetch_related(
            "decisions",
            "plot_search_targets__info_links",
            "plot_search_targets__plan_unit__lease_area__lease__decisions__decision_maker",
            "plot_search_targets__plan_unit__lease_area__lease__decisions__type",
            "plot_search_targets__plan_unit__lease_area__lease__decisions__conditions",
            "plot_search_targets__plan_unit__lease_area__addresses",
            "form__sections__fields__choices",
            "form__sections__subsections__fields__choices",
            "form__sections__subsections__subsections__fields__choices",
            "form__sections__subsections__subsections__subsections",
        )

    def get_serializer_class(self):
        if self.action in ("create", "metadata"):
            return PlotSearchCreateSerializer

        if self.action in ("update", "partial_update"):
            return PlotSearchUpdateSerializer

        return PlotSearchRetrieveSerializer
