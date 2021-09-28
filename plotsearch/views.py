from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from rest_framework_gis.filters import InBBoxFilter

from field_permissions.viewsets import FieldPermissionsViewsetMixin
from leasing.viewsets.utils import AtomicTransactionModelViewSet, AuditLogMixin
from plotsearch.models import (
    PlotSearch,
    PlotSearchSubtype,
    PlotSearchTarget,
    TargetInfoLink,
)
from plotsearch.serializers import (
    PlotSearchCreateSerializer,
    PlotSearchListSerializer,
    PlotSearchRetrieveSerializer,
    PlotSearchSubtypeSerializer,
    PlotSearchTargetInfoLinkSerializer,
    PlotSearchTargetSerializer,
    PlotSearchUpdateSerializer,
)


class PlotSearchSubtypeViewSet(AtomicTransactionModelViewSet):
    queryset = PlotSearchSubtype.objects.all()
    serializer_class = PlotSearchSubtypeSerializer
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


class TargetInfoLinkViewSet(AtomicTransactionModelViewSet):
    queryset = TargetInfoLink.objects.all()
    serializer_class = PlotSearchTargetInfoLinkSerializer


class PlotSearchTargetViewSet(AtomicTransactionModelViewSet):
    queryset = PlotSearchTarget.objects.all().prefetch_related("info_links")
    serializer_class = PlotSearchTargetSerializer
