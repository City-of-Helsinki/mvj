from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet
from rest_framework_gis.filters import InBBoxFilter

from field_permissions.viewsets import FieldPermissionsViewsetMixin
from leasing.viewsets.utils import AtomicTransactionModelViewSet, AuditLogMixin
from plotsearch.models import PlotSearch, PlotSearchSubtype, PlotSearchTarget
from plotsearch.serializers import (
    PlotSearchCreateSerializer,
    PlotSearchListSerializer,
    PlotSearchRetrieveSerializer,
    PlotSearchSubtypeSerializer,
    PlotSearchTargetSerializer,
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


class PlotSearchViewSet(
    AuditLogMixin, FieldPermissionsViewsetMixin, AtomicTransactionModelViewSet
):
    queryset = PlotSearch.objects.all()
    serializer_class = PlotSearchRetrieveSerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter, InBBoxFilter)

    def get_serializer_class(self):
        if self.action in ("create", "metadata"):
            return PlotSearchCreateSerializer

        if self.action in ("update", "partial_update"):
            return PlotSearchUpdateSerializer

        if self.action == "list":
            return PlotSearchListSerializer

        return PlotSearchRetrieveSerializer


class PlotSearchTargetViewSet(AtomicTransactionModelViewSet):
    queryset = PlotSearchTarget.objects.all().prefetch_related("info_links")
    serializer_class = PlotSearchTargetSerializer
