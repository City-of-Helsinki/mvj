from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from rest_framework_gis.filters import InBBoxFilter

from field_permissions.viewsets import FieldPermissionsViewsetMixin
from leasing.models import (
    PlotSearch,
    PlotSearchStage,
    PlotSearchSubtype,
    PlotSearchType,
)
from leasing.serializers.plot_search import (
    PlotSearchCreateSerializer,
    PlotSearchListSerializer,
    PlotSearchRetrieveSerializer,
    PlotSearchStageSerializer,
    PlotSearchSubtypeSerializer,
    PlotSearchTypeSerializer,
    PlotSearchUpdateSerializer,
)

from .utils import AtomicTransactionModelViewSet, AuditLogMixin


class PlotSearchTypeViewSet(AtomicTransactionModelViewSet):
    queryset = PlotSearchType
    serializer_class = PlotSearchTypeSerializer


class PlotSearchSubtypeViewSet(AtomicTransactionModelViewSet):
    queryset = PlotSearchSubtype
    serializer_class = PlotSearchSubtypeSerializer


class PlotSearchStageViewSet(AtomicTransactionModelViewSet):
    queryset = PlotSearchStage
    serializer_class = PlotSearchStageSerializer


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
