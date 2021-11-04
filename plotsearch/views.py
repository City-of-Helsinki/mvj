from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.viewsets import GenericViewSet
from rest_framework_gis.filters import InBBoxFilter

from field_permissions.viewsets import FieldPermissionsViewsetMixin
from leasing.viewsets.utils import AtomicTransactionModelViewSet, AuditLogMixin
from plotsearch.models import PlotSearch, PlotSearchSubtype
from plotsearch.serializers import (
    PlotSearchCreateSerializer,
    PlotSearchRetrieveSerializer,
    PlotSearchSubtypeSerializer,
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
    queryset = PlotSearch.objects.all().prefetch_related("plot_search_targets")
    serializer_class = PlotSearchRetrieveSerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter, InBBoxFilter)
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def get_serializer_class(self):
        if self.action in ("create", "metadata"):
            return PlotSearchCreateSerializer

        if self.action in ("update", "partial_update"):
            return PlotSearchUpdateSerializer

        return PlotSearchRetrieveSerializer
