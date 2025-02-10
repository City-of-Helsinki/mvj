import io
import zipfile
from datetime import datetime
from typing import Any, Dict
from zipfile import ZipInfo

import xlsxwriter
from django import http
from django.http import HttpResponse, QueryDict
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend
from django_filters.views import FilterView
from django_xhtml2pdf.views import PdfMixin
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_gis.filters import InBBoxFilter

from field_permissions.viewsets import FieldPermissionsViewsetMixin
from file_operations.errors import FileScanError, FileScanPendingError, FileUnsafeError
from file_operations.viewsets.mixins import (
    FileExtensionFileMixin,
    FileMixin,
    get_filescan_error_response,
)
from forms.models import Answer
from forms.serializers.form import AnswerOpeningRecordSerializer
from leasing.models import CustomDetailedPlan
from leasing.permissions import (
    MvjDjangoModelPermissions,
    MvjDjangoModelPermissionsOrAnonReadOnly,
    PerMethodPermission,
)
from leasing.viewsets.utils import AtomicTransactionModelViewSet
from plotsearch.enums import SearchStage
from plotsearch.filter import (
    AreaSearchFilterSet,
    InformationCheckListFilterSet,
    PlotSearchFilterSet,
    PlotSearchPublicFilterSet,
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
    RelatedPlotApplication,
    TargetStatus,
)
from plotsearch.models.plot_search import (
    FAQ,
    AreaSearchAttachment,
    DirectReservationLink,
)
from plotsearch.permissions import (
    AreaSearchAttachmentPublicPermissions,
    AreaSearchPublicPermissions,
    PlotSearchOpeningRecordPermissions,
)
from plotsearch.serializers.plot_search import (
    AreaSearchAttachmentPublicSerializer,
    AreaSearchAttachmentSerializer,
    AreaSearchDetailSerializer,
    AreaSearchListSerializer,
    AreaSearchPublicSerializer,
    AreaSearchSerializer,
    DirectReservationLinkSerializer,
    FAQSerializer,
    FavouriteSerializer,
    InformationCheckSerializer,
    IntendedUsePlotsearchPublicSerializer,
    IntendedUseSerializer,
    PlotSearchCreateSerializer,
    PlotSearchFilterSerializer,
    PlotSearchPublicSerializer,
    PlotSearchRetrieveSerializer,
    PlotSearchStageSerializer,
    PlotSearchSubtypeSerializer,
    PlotSearchTargetSerializer,
    PlotSearchTypeSerializer,
    PlotSearchUpdateSerializer,
    RelatedPlotApplicationCreateDeleteSerializer,
)
from plotsearch.utils import build_pdf_context


class PlotSearchSubtypeViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    queryset = PlotSearchSubtype.objects.all()
    serializer_class = PlotSearchSubtypeSerializer
    permission_classes = (MvjDjangoModelPermissions,)
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_fields = ["plot_search_type"]


class PlotSearchSubtypePublicViewSet(PlotSearchSubtypeViewSet):
    permission_classes = (MvjDjangoModelPermissionsOrAnonReadOnly,)


class PlotSearchTypeViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    queryset = PlotSearchType.objects.all()
    serializer_class = PlotSearchTypeSerializer
    permission_classes = (MvjDjangoModelPermissions,)

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.prefetch_related("plotsearchsubtype_set")


class PlotSearchTypePublicViewSet(PlotSearchTypeViewSet):
    permission_classes = (MvjDjangoModelPermissionsOrAnonReadOnly,)


class PlotSearchStageViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    queryset = PlotSearchStage.objects.all()
    serializer_class = PlotSearchStageSerializer
    permission_classes = (MvjDjangoModelPermissions,)


class PlotSearchStagePublicViewSet(PlotSearchStageViewSet):
    permission_classes = (MvjDjangoModelPermissionsOrAnonReadOnly,)


class PlotSearchViewSet(FieldPermissionsViewsetMixin, AtomicTransactionModelViewSet):
    queryset = PlotSearch.objects.all()
    serializer_class = PlotSearchRetrieveSerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter, InBBoxFilter)
    permission_classes = (MvjDjangoModelPermissions,)
    filterset_class = PlotSearchFilterSet

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
        if (
            self.action == "list"
            and self.request.query_params.get("name")
            and len(self.request.query_params.get("name")) > 1
        ):
            return PlotSearchFilterSerializer
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

    @action(
        methods=["post"],
        detail=True,
        serializer_class=AnswerOpeningRecordSerializer,
        permission_classes=(PlotSearchOpeningRecordPermissions,),
    )
    def open_answers(self, request, pk=None):
        plot_search = self.get_object()
        answer_qs = Answer.objects.filter(
            targets__in=plot_search.plot_search_targets.all()
        ).exclude(opening_record__isnull=False)

        serializer = AnswerOpeningRecordSerializer
        if isinstance(request.data, QueryDict):
            request_data = request.data.dict()
        else:
            request_data = request.data

        for answer in answer_qs:
            request_data["answer"] = answer.pk
            aor_serializer = serializer(
                data=request_data, context=self.get_serializer_context()
            )
            aor_serializer.is_valid()
            aor_serializer.save()
        return HttpResponse(status=204)


class PlotSearchPublicViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PlotSearch.objects.filter(
        stage__stage=SearchStage.IN_ACTION,  # IMPORTANT: Only active plot searches are public!
    )
    serializer_class = PlotSearchPublicSerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter, InBBoxFilter)
    permission_classes = (MvjDjangoModelPermissionsOrAnonReadOnly,)
    filterset_class = PlotSearchPublicFilterSet

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.prefetch_related(
            "plot_search_targets__info_links",
            "plot_search_targets__plan_unit__lease_area__lease__decisions__decision_maker",
            "plot_search_targets__plan_unit__lease_area__lease__decisions__type",
            "plot_search_targets__plan_unit__lease_area__lease__decisions__conditions",
            "plot_search_targets__plan_unit__lease_area__addresses",
        ).select_related("form")

    def get_serializer_class(self):
        return PlotSearchPublicSerializer


class PlotSearchUIDataView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        aggregated_data = {
            "plot_search": PlotSearch.objects.filter(
                search_class="plot_search",
                begin_at__lte=datetime.now(),
                end_at__gte=datetime.now(),
            ).count(),
            "other_search": PlotSearch.objects.filter(
                search_class="other_search",
                begin_at__lte=datetime.now(),
                end_at__gte=datetime.now(),
            ).count(),
        }

        return Response(aggregated_data)


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


class IntendedUsePlotsearchViewSet(IntendedUseViewSet):
    permission_classes = (MvjDjangoModelPermissions,)


class IntendedUsePlotsearchPublicViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    queryset = AreaSearchIntendedUse.objects.all()
    serializer_class = IntendedUsePlotsearchPublicSerializer
    permission_classes = (IsAuthenticated,)


class AreaSearchViewSet(viewsets.ModelViewSet):
    queryset = AreaSearch.objects.filter(answer__isnull=False).prefetch_related(
        "area_search_status__status_notes__preparer",
        "answer__entry_sections",
    )
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
    ordering = "-received_date"
    bbox_filter_field = "geometry"
    bbox_filter_include_overlapping = True

    def get_serializer_class(self):
        if self.action == "retrieve":
            return AreaSearchDetailSerializer
        if self.action == "list":
            return AreaSearchListSerializer
        return super().get_serializer_class()

    @action(methods=["get"], detail=False)
    def get_answers_xlsx(self, *args, **kwargs):
        area_search_qs = self.filter_queryset(self.get_queryset())

        output = io.BytesIO()

        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet()

        row = 0

        for area_search in area_search_qs:
            worksheet, row = area_search.get_xlsx_page(worksheet, row)

        workbook.close()

        output.seek(0)

        response = HttpResponse(
            output,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = (
            'attachment; filename="Applications-{}.xlsx"'.format(
                timezone.now().isoformat("T")
            )
        )

        return response


class AreaSearchPublicViewSet(
    mixins.CreateModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet
):
    queryset = AreaSearch.objects.all()
    serializer_class = AreaSearchPublicSerializer
    permission_classes = (
        AreaSearchPublicPermissions,
        IsAuthenticated,
    )
    filter_backends = (DjangoFilterBackend, OrderingFilter, InBBoxFilter)
    filterset_class = AreaSearchFilterSet
    bbox_filter_field = "geometry"
    bbox_filter_include_overlapping = True

    def get_permissions(self):
        return [permission() for permission in self.permission_classes]


class AreaSearchAttachmentViewset(
    FileMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    queryset = AreaSearchAttachment.objects.all()
    serializer_class = AreaSearchAttachmentSerializer
    permission_classes = (PerMethodPermission,)
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
        if user.has_perm("plotsearch.view_areasearchattachment"):
            return qs
        return qs.filter(user=self.request.user)

    @action(methods=["get"], detail=True)
    def download(self, request, pk=None):
        """Needed to inform FileDownloadMixin of which field holds the file."""
        return super().download(request, pk, file_field="attachment")


class AreaSearchAttachmentPublicViewset(
    FileExtensionFileMixin, AreaSearchAttachmentViewset
):
    """Includes FileExtensionFileMixin to validate file extensions."""

    serializer_class = AreaSearchAttachmentPublicSerializer
    permission_classes = (AreaSearchAttachmentPublicPermissions,)

    def destroy(self, request, *args, **kwargs):
        raise MethodNotAllowed("DELETE")


class InformationCheckViewSet(
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


class TargetStatusGeneratePDF(PdfMixin, FilterView, APIView):
    permission_classes = (MvjDjangoModelPermissions,)
    template_name = "target_status/detail.html"
    model = TargetStatus
    filterset_class = TargetStatusExportFilterSet

    @staticmethod
    def get_nested_attr(obj, attrs: str, default=None):
        """Get nested attribute described with dot separated string from an object.
        E.g. 'company.address.city'"""
        for attr in attrs.split("."):
            try:
                obj = getattr(obj, attr)
            except AttributeError:
                return default
        return obj

    def _get_plan(self, object: TargetStatus):
        """Get either PlanUnit or CustomDetailedPlan from TargetStatus's PlotSearchTarget."""
        plan_unit = self.get_nested_attr(object, "plot_search_target.plan_unit")
        custom_detailed_plan = self.get_nested_attr(
            object, "plot_search_target.custom_detailed_plan"
        )
        return plan_unit if plan_unit else custom_detailed_plan

    def _get_plan_intended_use(self, object):
        """Get intended use from either Plan or PlanUnit."""
        for attr in ("intended_use", "plan_unit_intended_use"):
            try:
                return getattr(self._get_plan(object), attr)
            except AttributeError:
                continue
        return None

    def _get_plot_search_information(self, object):
        """Creates plot search information context for PDF template.
        Generates a list of dictionarys, excluding those without a value."""
        plan = self._get_plan(object)
        plan_intended_use = self._get_plan_intended_use(object)

        plot_identifier = getattr(plan, "identifier", None)
        try:
            application_deadline = self.get_nested_attr(
                object, "plot_search_target.plot_search.end_at"
            ).strftime("%H:%M %d.%m.%Y")
        except AttributeError:
            application_deadline = None

        address = getattr(plan.lease_area.addresses.first(), "address", None)
        detailed_plan_identifier = (
            getattr(plan, "detailed_plan_identifier", None)
            or getattr(plan, "identifier", None)
            if isinstance(plan, CustomDetailedPlan)
            else None
        )
        detailed_plan_state = self.get_nested_attr(
            plan, "state.name"
        ) or self.get_nested_attr(plan, "plan_unit_state.name")
        intended_use = getattr(plan_intended_use, "name")
        # Comes from CustomDetailedPlan only
        rent_build_permission = getattr(plan, "rent_build_permission", None)
        area = getattr(plan, "area", None) or self.get_nested_attr(
            plan, "lease_area.area"
        )
        # Unknown where this comes from, but it is used in the UI
        first_suitable_construction_year = getattr(
            plan, "first_suitable_construction_year", None
        )
        lease_hitas = getattr(plan, "lease_area.lease.hitas.name", None)
        lease_financing = getattr(plan, "lease_area.lease.financing.name", None)
        lease_management = getattr(plan, "lease_area.lease.management.name", None)

        plotsearch_info = [
            {
                "label": _("The deadline for applications"),
                "value": application_deadline,
            },
            {"label": _("Plot"), "value": plot_identifier},
            {"label": _("Address"), "value": address},
            {
                "label": _("Detailed plan identifier"),
                "value": detailed_plan_identifier,
            },
            {"label": _("Detailed plan state"), "value": detailed_plan_state},
            {"label": _("Intended use"), "value": intended_use},
            {
                "label": _("Permitted build floor area (floor-m²)"),
                "value": rent_build_permission,
            },
            {  # The value is defined in public-ui but not used
                "label": _("Permitted build residential floor area (floor-m²)"),
                "value": None,
            },
            {  # The value is defined in public-ui but not used
                "label": _("Permitted build commercial floor area (floor-m²)"),
                "value": None,
            },
            {"label": _("Area (m²)"), "value": area},
            {
                "label": _("First suitable construction year"),
                "value": first_suitable_construction_year,
            },
            {"label": _("HITAS"), "value": lease_hitas},
            {"label": _("Financing method"), "value": lease_financing},
            {"label": _("Management method"), "value": lease_management},
        ]

        return [x for x in plotsearch_info if x["value"] is not None]

    def render_to_response(
        self, context: Dict[str, Any], **response_kwargs: Any
    ) -> http.HttpResponse:
        response_kwargs.setdefault("content_type", self.content_type)
        response = HttpResponse(content_type="application/zip")
        with zipfile.PyZipFile(response, mode="w") as zip_file:
            for object in self.object_list:
                context.update(object=object)
                context.update(
                    plotsearch_info=self._get_plot_search_information(object)
                )
                pdf_response = self.response_class(
                    request=self.request,
                    template=self.get_template_names(),
                    context=build_pdf_context(context),
                    using=self.template_engine,
                    **response_kwargs,
                )
                zip_file.writestr(
                    ZipInfo("{}.pdf".format(object.application_identifier)),
                    pdf_response.render().content,
                )

        response["Content-Disposition"] = (
            f'attachment; filename={"{}.zip".format(self.object_list[0].plot_search_target.plot_search.name)}'
        )

        return response


class AreaSearchGeneratePDF(PdfMixin, FilterView, APIView):
    permission_classes = (MvjDjangoModelPermissions,)
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
                information_checks = InformationCheck.objects.filter(
                    entry_section__in=object.answer.entry_sections.all()
                )
                context.update(
                    object=object,
                    information_checks=information_checks,
                )
                pdf_response = self.response_class(
                    request=self.request,
                    template=self.get_template_names(),
                    context=build_pdf_context(context),
                    using=self.template_engine,
                    **response_kwargs,
                )
                zip_file.writestr(
                    ZipInfo("{}.pdf".format(object.identifier)),
                    pdf_response.render().content,
                )
                if self.request.GET.get("show_attachments", False):
                    for attachment in object.area_search_attachments.all():
                        try:
                            file = attachment.attachment.open()
                            zip_file.writestr(
                                ZipInfo(
                                    "{} {}".format(
                                        object.identifier, attachment.attachment.name
                                    )
                                ),
                                file.file.file.read(),
                            )
                        except (
                            FileScanPendingError,
                            FileUnsafeError,
                            FileScanError,
                        ) as e:
                            return get_filescan_error_response(e)

        response["Content-Disposition"] = (
            f'attachment; filename={"{}.zip".format(self.object_list[0].lessor)}'
        )

        return response


"""
class DebugAreaSearchPDF(generic.DetailView):
    model = AreaSearch
    template_name = "area_search/detail.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        return build_pdf_context(context)
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


class RelatedPlotApplicationViewSet(viewsets.ModelViewSet):
    queryset = RelatedPlotApplication.objects.all()
    serializer_class = RelatedPlotApplicationCreateDeleteSerializer
    permission_classes = (MvjDjangoModelPermissions,)
