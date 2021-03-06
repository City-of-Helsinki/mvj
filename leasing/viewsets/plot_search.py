from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from rest_framework_gis.filters import InBBoxFilter

from field_permissions.viewsets import FieldPermissionsViewsetMixin
from leasing.models import PlotSearch, PlotSearchSubtype
from leasing.serializers.plot_search import (
    PlotSearchCreateSerializer,
    PlotSearchListSerializer,
    PlotSearchRetrieveSerializer,
    PlotSearchSubtypeSerializer,
    PlotSearchUpdateSerializer,
)

from .utils import AtomicTransactionModelViewSet, AuditLogMixin


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
