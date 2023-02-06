import io
import zipfile
from typing import Any, Dict
from zipfile import ZipInfo

import xlsxwriter
from django import http
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from django_filters.views import FilterView
from django_xhtml2pdf.views import PdfMixin
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework_gis.filters import InBBoxFilter

from field_permissions.viewsets import FieldPermissionsViewsetMixin
from leasing.permissions import (
    MvjDjangoModelPermissions,
    MvjDjangoModelPermissionsOrAnonReadOnly,
)
from leasing.viewsets.utils import AtomicTransactionModelViewSet, AuditLogMixin
from plotsearch.filter import InformationCheckListFilterSet, TargetStatusExportFilterSet
from plotsearch.models import (
    AreaSearch,
    Favourite,
    InformationCheck,
    IntendedSubUse,
    IntendedUse,
    PlotSearch,
    PlotSearchStage,
    PlotSearchSubtype,
    PlotSearchType, TargetStatus,
)
from plotsearch.serializers.plot_search import (
    AreaSearchSerializer,
    FavouriteSerializer,
    InformationCheckSerializer,
    IntendedSubUseSerializer,
    IntendedUseSerializer,
    PlotSearchCreateSerializer,
    PlotSearchRetrieveSerializer,
    PlotSearchStageSerializer,
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


class PlotSearchStageViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    queryset = PlotSearchStage.objects.all()
    serializer_class = PlotSearchStageSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)


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

    @action(methods=["get"], detail=True)
    def get_answers_xlsx(self, *args, **kwargs):
        plotsearch = self.get_object()
        plot_search_targets = plotsearch.plot_search_targets.all()

        output = io.BytesIO()

        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet()

        row = 0

        for plot_search_target in plot_search_targets:
            for target_status in plot_search_target.statuses.all():
                worksheet, row = target_status.target_status_get_xlsx_page(worksheet, row)

        workbook.close()

        output.seek(0)

        response = HttpResponse(output, content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response["Content-Disposition"] = 'attachment; filename="Applications.xlsx"'

        return response



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
    AuditLogMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = InformationCheck.objects.all()
    serializer_class = InformationCheckSerializer
    permission_classes = (MvjDjangoModelPermissions,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = InformationCheckListFilterSet


class GeneratePDF(PdfMixin, FilterView):
    template_name = 'target_status/detail.html'
    model = TargetStatus
    filterset_class = TargetStatusExportFilterSet

    def render_to_response(self, context: Dict[str, Any], **response_kwargs: Any) -> http.HttpResponse:
        response_kwargs.setdefault('content_type', self.content_type)
        response = HttpResponse(content_type='application/zip')
        with zipfile.PyZipFile(response, mode="w") as zip_file:
            for object in self.object_list:
                context.update(object=object)
                pdf_response = self.response_class(
                    request=self.request,
                    template=self.get_template_names(),
                    context=context,
                    using=self.template_engine,
                    **response_kwargs
                )
                zip_file.writestr(ZipInfo("{}.pdf".format(object.application_identifier)), pdf_response.render().content)

        response['Content-Disposition'] = f'attachment; filename={"{}.zip".format(self.object_list[0].plot_search_target.plot_search.name)}'

        return response


