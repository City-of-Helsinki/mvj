import io
import zipfile
from typing import Any, Dict
from zipfile import ZipInfo

import xlsxwriter
from django import http
from django.core.files import File
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from django_filters.views import FilterView
from django_xhtml2pdf.views import PdfMixin
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_gis.filters import InBBoxFilter

from field_permissions.viewsets import FieldPermissionsViewsetMixin
from leasing.permissions import (
    MvjDjangoModelPermissions,
    MvjDjangoModelPermissionsOrAnonReadOnly,
    PerMethodPermission,
)
from leasing.viewsets.utils import AtomicTransactionModelViewSet, AuditLogMixin
from plotsearch.filter import (
    AreaSearchFilterSet,
    InformationCheckListFilterSet,
    TargetStatusExportFilterSet,
)
from plotsearch.models import (
    AreaSearch,
    AreaSearchIntendedUse,
    Favourite,
    FavouriteTarget,
    InformationCheck,
    PlotSearch,
    PlotSearchStage,
    PlotSearchSubtype,
    PlotSearchTarget,
    PlotSearchType,
    TargetStatus,
)
from plotsearch.models.plot_search import (
    FAQ,
    AreaSearchAttachment,
    DirectReservationLink,
)
from plotsearch.permissions import AreaSearchAttachmentPermissions
from plotsearch.serializers.plot_search import (
    AreaSearchAttachmentSerializer,
    AreaSearchDetailSerializer,
    AreaSearchSerializer,
    DirectReservationLinkSerializer,
    FAQSerializer,
    FavouriteSerializer,
    InformationCheckSerializer,
    IntendedUseSerializer,
    PlotSearchCreateSerializer,
    PlotSearchRetrieveSerializer,
    PlotSearchStageSerializer,
    PlotSearchSubtypeSerializer,
    PlotSearchTargetSerializer,
    PlotSearchTypeSerializer,
    PlotSearchUpdateSerializer,
)
from plotsearch.utils import get_applicant_type


class PlotSearchSubtypeViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    queryset = PlotSearchSubtype.objects.all()
    serializer_class = PlotSearchSubtypeSerializer
    permission_classes = (MvjDjangoModelPermissionsOrAnonReadOnly,)
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_fields = ["plot_search_type"]


class PlotSearchTypeViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    queryset = PlotSearchType.objects.all()
    serializer_class = PlotSearchTypeSerializer
    permission_classes = (MvjDjangoModelPermissionsOrAnonReadOnly,)

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.prefetch_related("plotsearchsubtype_set")


class PlotSearchStageViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    queryset = PlotSearchStage.objects.all()
    serializer_class = PlotSearchStageSerializer
    permission_classes = (MvjDjangoModelPermissionsOrAnonReadOnly,)


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
                worksheet, row = target_status.target_status_get_xlsx_page(
                    worksheet, row
                )

        workbook.close()

        output.seek(0)

        response = HttpResponse(
            output,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = 'attachment; filename="Applications.xlsx"'

        return response


class PlotSearchTargetViewSet(mixins.UpdateModelMixin, viewsets.GenericViewSet):
    queryset = PlotSearchTarget.objects.all()
    serializer_class = PlotSearchTargetSerializer
    permission_classes = (IsAuthenticated,)


class FavouriteViewSet(viewsets.ModelViewSet):
    queryset = Favourite.objects.all()
    serializer_class = FavouriteSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(user=self.request.user).prefetch_related("targets")


class IntendedUseViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    queryset = AreaSearchIntendedUse.objects.all()
    serializer_class = IntendedUseSerializer
    permission_classes = (MvjDjangoModelPermissionsOrAnonReadOnly,)


class AreaSearchViewSet(viewsets.ModelViewSet):
    queryset = AreaSearch.objects.filter(answer__isnull=False)
    serializer_class = AreaSearchSerializer
    permission_classes = (PerMethodPermission,)
    perms_map = {
        "GET": ["plotsearch.view_areasearch"],
        "HEAD": ["plotsearch.view_areasearch"],
        "PUT": ["plotsearch.change_areasearch"],
        "PATCH": ["plotsearch.change_areasearch"],
        "DELETE": ["plotsearch.delete_areasearch"],
    }
    filter_backends = (DjangoFilterBackend, OrderingFilter, InBBoxFilter)
    filterset_class = AreaSearchFilterSet
    bbox_filter_field = "geometry"
    bbox_filter_include_overlapping = True

    def get_serializer_class(self):
        if self.action == "retrieve":
            return AreaSearchDetailSerializer
        return super().get_serializer_class()


class AreaSearchAttachmentViewset(
    mixins.CreateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet
):
    queryset = AreaSearchAttachment.objects.all()
    serializer_class = AreaSearchAttachmentSerializer
    permission_classes = (AreaSearchAttachmentPermissions,)
    perms_map = {
        "GET": ["plotsearch.view_areasearchattachment"],
        "HEAD": ["plotsearch.view_areasearchattachment"],
        "PUT": ["plotsearch.change_areasearchattachment"],
        "PATCH": ["plotsearch.change_areasearchattachment"],
        "DELETE": ["plotsearch.delete_areasearchattachment"],
    }

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.has_perm("plot_search.area_search_attachment"):
            return qs
        return qs.filter(user=self.request.user)

    @action(methods=["get"], detail=True)
    def download(self, request, pk=None):
        obj = self.get_object()

        with obj.attachment.open() as fp:
            # TODO: detect file MIME type
            response = HttpResponse(File(fp), content_type="application/octet-stream")
            response["Content-Disposition"] = 'attachment; filename="{}"'.format(
                obj.name
            )

            return response


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


class DirectReservationLinkViewSet(viewsets.ModelViewSet):
    queryset = DirectReservationLink.objects.all()
    serializer_class = DirectReservationLinkSerializer
    permission_classes = (MvjDjangoModelPermissions,)


class TargetStatusGeneratePDF(PdfMixin, FilterView):
    template_name = "target_status/detail.html"
    model = TargetStatus
    filterset_class = TargetStatusExportFilterSet

    def render_to_response(
        self, context: Dict[str, Any], **response_kwargs: Any
    ) -> http.HttpResponse:
        response_kwargs.setdefault("content_type", self.content_type)
        response = HttpResponse(content_type="application/zip")
        with zipfile.PyZipFile(response, mode="w") as zip_file:
            for object in self.object_list:
                context.update(object=object)
                pdf_response = self.response_class(
                    request=self.request,
                    template=self.get_template_names(),
                    context=context,
                    using=self.template_engine,
                    **response_kwargs,
                )
                zip_file.writestr(
                    ZipInfo("{}.pdf".format(object.application_identifier)),
                    pdf_response.render().content,
                )

        response[
            "Content-Disposition"
        ] = f'attachment; filename={"{}.zip".format(self.object_list[0].plot_search_target.plot_search.name)}'

        return response


class AreaSearchGeneratePDF(PdfMixin, FilterView):
    template_name = "area_search/detail.html"
    model = AreaSearch
    filterset_class = AreaSearchFilterSet

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        show_information_check = self.request.GET.get("show_information_check", False)

        context.update({"show_information_check": show_information_check})

        return context

    def render_to_response(
        self, context: Dict[str, Any], **response_kwargs: Any
    ) -> http.HttpResponse:
        response_kwargs.setdefault("content_type", self.content_type)
        response = HttpResponse(content_type="application/zip")
        with zipfile.PyZipFile(response, mode="w") as zip_file:
            for object in self.object_list:
                context.update(
                    object=object, applicant_type=get_applicant_type(object.answer)
                )
                pdf_response = self.response_class(
                    request=self.request,
                    template=self.get_template_names(),
                    context=context,
                    using=self.template_engine,
                    **response_kwargs,
                )
                zip_file.writestr(
                    ZipInfo("{}.pdf".format(object.identifier)),
                    pdf_response.render().content,
                )

        response[
            "Content-Disposition"
        ] = f'attachment; filename={"{}.zip".format(self.object_list[0].lessor)}'

        return response


"""
# For PDF debugging purposes
class DebugAreaSearchPDF(generic.DetailView):
    model = AreaSearch
    template_name = "area_search/detail.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(applicant_type=get_applicant_type(context["areasearch"].answer))
        return context
"""


class DirectReservationToFavourite(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        Favourite.objects.filter(user=request.user).delete()
        direct_reservation_link = DirectReservationLink.objects.get(uuid=kwargs["uuid"])
        favourite = Favourite.objects.create(user=request.user)
        targets = []
        for plot_search_target in direct_reservation_link.targets.all():
            target, created = FavouriteTarget.objects.get_or_create(
                favourite=favourite, plot_search_target=plot_search_target
            )
            if created:
                targets.append(target)
        for target in targets:
            target.refresh_from_db()

        return Response(FavouriteSerializer(favourite).data, status=200)


class FAQViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = FAQ.objects.all()
    permission_classes = (MvjDjangoModelPermissionsOrAnonReadOnly,)
    serializer_class = FAQSerializer
