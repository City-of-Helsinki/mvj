from rest_framework import filters, mixins
from rest_framework.decorators import action
from rest_framework.viewsets import GenericViewSet

from field_permissions.viewsets import FieldPermissionsViewsetMixin
from file_operations.viewsets.mixins import FileMixin
from leasing.models import LeaseAreaAttachment
from leasing.models.land_area import CustomDetailedPlan, PlanUnit, Plot
from leasing.serializers.land_area import (
    CustomDetailedPlanListWithIdentifiersSerializer,
    CustomDetailedPlanSerializer,
    LeaseAreaAttachmentCreateUpdateSerializer,
    LeaseAreaAttachmentSerializer,
    PlanUnitListWithIdentifiersSerializer,
    PlanUnitSerializer,
    PlotIdentifierSerializer,
)
from plotsearch.models import PlotSearch, PlotSearchTarget

from .utils import AtomicTransactionModelViewSet, MultiPartJsonParser


class LeaseAreaAttachmentViewSet(
    FileMixin,
    FieldPermissionsViewsetMixin,
    AtomicTransactionModelViewSet,
):
    queryset = LeaseAreaAttachment.objects.all()
    serializer_class = LeaseAreaAttachmentSerializer
    parser_classes = (MultiPartJsonParser,)

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update", "metadata"):
            return LeaseAreaAttachmentCreateUpdateSerializer

        return LeaseAreaAttachmentSerializer

    @action(methods=["get"], detail=True)
    def download(self, request, pk=None):
        """Needed to inform FileDownloadMixin of which field holds the file."""
        return super().download(request, pk, file_field="file")


class PlanUnitViewSet(mixins.RetrieveModelMixin, GenericViewSet):
    queryset = PlanUnit.objects.all()
    serializer_class = PlanUnitSerializer


class CustomDetailedPlanViewSet(mixins.RetrieveModelMixin, GenericViewSet):
    queryset = CustomDetailedPlan.objects.all()
    serializer_class = CustomDetailedPlanSerializer


class PlanUnitListWithIdentifiersViewSet(mixins.ListModelMixin, GenericViewSet):
    search_fields = [
        "^lease_area__lease__identifier__identifier",
        "^lease_area__identifier",
        "^identifier",
    ]
    filter_backends = (filters.SearchFilter,)
    queryset = PlanUnit.objects.all()
    serializer_class = PlanUnitListWithIdentifiersSerializer

    def get_queryset(self):
        # PlotSearch.objects.all() is important command as PlotSearch is SafeDeleteModel
        plan_unit_ids = PlotSearchTarget.objects.filter(
            plan_unit__isnull=False, plot_search__in=PlotSearch.objects.all()
        ).values("plan_unit__identifier")
        return (
            super()
            .get_queryset()
            .filter(is_master=True)
            .exclude(identifier__in=plan_unit_ids)
            .select_related("lease_area")
            .only(
                "id",
                "identifier",
                "plan_unit_status",
                "lease_area__identifier",
                "lease_area__lease__identifier__identifier",
            )
        )


class CustomDetailedPlanListWithIdentifiersViewSet(
    mixins.ListModelMixin, GenericViewSet
):
    search_fields = [
        "^lease_area__lease__identifier__identifier",
        "^lease_area__identifier",
        "^identifier",
    ]
    filter_backends = (filters.SearchFilter,)
    queryset = CustomDetailedPlan.objects.all()
    serializer_class = CustomDetailedPlanListWithIdentifiersSerializer

    def get_queryset(self):
        # PlotSearch.objects.all() is important command as PlotSearch is SafeDeleteModel
        custom_detailed_plan_ids = PlotSearchTarget.objects.filter(
            custom_detailed_plan__isnull=False, plot_search__in=PlotSearch.objects.all()
        ).values("custom_detailed_plan__identifier")
        return (
            super()
            .get_queryset()
            .exclude(identifier__in=custom_detailed_plan_ids)
            .select_related("lease_area")
            .only(
                "id",
                "identifier",
                "state",
                "lease_area__identifier",
                "lease_area__lease__identifier__identifier",
            )
        )


class PlotMasterIdentifierList(mixins.ListModelMixin, GenericViewSet):
    search_fields = [
        "^identifier",
    ]
    filter_backends = (filters.SearchFilter,)
    queryset = Plot.objects.all()
    serializer_class = PlotIdentifierSerializer

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(is_master=True)
            .only(
                "id",
                "identifier",
            )
        )
