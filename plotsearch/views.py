from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, viewsets
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework_gis.filters import InBBoxFilter

from field_permissions.viewsets import FieldPermissionsViewsetMixin
from leasing.permissions import (
    MvjDjangoModelPermissions,
    MvjDjangoModelPermissionsOrAnonReadOnly,
)
from leasing.viewsets.utils import AtomicTransactionModelViewSet, AuditLogMixin
from plotsearch.models import (
    AreaSearch,
    Favourite,
    InformationCheck,
    IntendedSubUse,
    IntendedUse,
    PlotSearch,
    PlotSearchSubtype,
    PlotSearchType,
)
from plotsearch.serializers import (
    AreaSearchSerializer,
    FavouriteSerializer,
    InformationCheckSerializer,
    IntendedSubUseSerializer,
    IntendedUseSerializer,
    PlotSearchCreateSerializer,
    PlotSearchRetrieveSerializer,
    PlotSearchSubtypeSerializer,
    PlotSearchTypeSerializer,
    PlotSearchUpdateSerializer,
)


class PlotSearchSubtypeViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    queryset = PlotSearchSubtype.objects.all()
    serializer_class = PlotSearchSubtypeSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_fields = ["plot_search_type"]


class PlotSearchTypeViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    queryset = PlotSearchType.objects.all()
    serializer_class = PlotSearchTypeSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)

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
        ).select_related("form")

    def get_serializer_class(self):
        if self.action in ("create", "metadata"):
            return PlotSearchCreateSerializer

        if self.action in ("update", "partial_update"):
            return PlotSearchUpdateSerializer

        return PlotSearchRetrieveSerializer


class FavouriteViewSet(viewsets.ModelViewSet):
    queryset = Favourite.objects.all()
    serializer_class = FavouriteSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(user=self.request.user).prefetch_related("targets")


class IntendedSubUseViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    queryset = IntendedSubUse.objects.all()
    serializer_class = IntendedSubUseSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_fields = ["intended_use"]


class IntendedUseViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    queryset = IntendedUse.objects.all()
    serializer_class = IntendedUseSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.prefetch_related("intendedsubuse_set")


class AreaSearchViewSet(viewsets.ModelViewSet):
    queryset = AreaSearch.objects.all()
    serializer_class = AreaSearchSerializer
    permission_classes = (IsAuthenticated,)


class InformationCheckViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = InformationCheck.objects.all()
    serializer_class = InformationCheckSerializer
    permission_classes = (MvjDjangoModelPermissions,)
