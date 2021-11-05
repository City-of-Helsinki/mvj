from django.db.models import Prefetch
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.viewsets import GenericViewSet
from rest_framework_gis.filters import InBBoxFilter

from field_permissions.viewsets import FieldPermissionsViewsetMixin
from leasing.models import Decision, Lease, LeaseArea, PlanUnit
from leasing.viewsets.utils import AtomicTransactionModelViewSet, AuditLogMixin
from plotsearch.models import PlotSearch, PlotSearchSubtype, PlotSearchTarget
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
    queryset = PlotSearch.objects.prefetch_related(
        "decisions",
        Prefetch(
            "plot_search_targets",
            queryset=PlotSearchTarget.objects.prefetch_related(
                Prefetch(
                    "plan_unit",
                    queryset=PlanUnit.objects.prefetch_related(
                        Prefetch(
                            "lease_area",
                            queryset=LeaseArea.objects.prefetch_related(
                                Prefetch(
                                    "lease",
                                    queryset=Lease.objects.prefetch_related(
                                        Prefetch(
                                            "decisions",
                                            queryset=Decision.objects.prefetch_related(
                                                "decision_maker", "type", "conditions",
                                            ),
                                        )
                                    ),
                                )
                            ),
                        )
                    ),
                )
            ),
        ),
    )
    serializer_class = PlotSearchRetrieveSerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter, InBBoxFilter)
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def get_serializer_class(self):
        if self.action in ("create", "metadata"):
            return PlotSearchCreateSerializer

        if self.action in ("update", "partial_update"):
            return PlotSearchUpdateSerializer

        return PlotSearchRetrieveSerializer
