from django.core.files import File
from django.db.models import Prefetch
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from forms.filter import AnswerFilterSet, TargetStatusFilterSet
from forms.models import Answer, Entry, Form
from forms.models.form import Attachment
from forms.permissions import TargetStatusPermissions
from forms.serializers.form import (
    AnswerListSerializer,
    AnswerSerializer,
    AttachmentSerializer,
    FormSerializer,
    MeetingMemoSerializer,
    ReadAttachmentSerializer,
    TargetStatusListSerializer,
    TargetStatusUpdateSerializer,
)
from forms.utils import AnswerInBBoxFilter
from leasing.permissions import (
    MvjDjangoModelPermissions,
    MvjDjangoModelPermissionsOrAnonReadOnly,
)
from plotsearch.models import TargetStatus
from plotsearch.models.plot_search import MeetingMemo


class FormViewSet(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    # create is disabled
    # TODO: Add permission check for delete and edit functions to prevent deleting template forms (is_template = True)
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["is_template"]
    serializer_class = FormSerializer
    permission_classes = (MvjDjangoModelPermissionsOrAnonReadOnly,)

    def get_queryset(self):
        queryset = Form.objects.prefetch_related(
            "sections__fields__choices",
            "sections__subsections__fields__choices",
            "sections__subsections__subsections__fields__choices",
            "sections__subsections__subsections__subsections",
        )
        return queryset


class AnswerViewSet(viewsets.ModelViewSet):
    queryset = (
        Answer.objects.all()
        .prefetch_related(
            "entry_sections",
            "targets",
            "statuses",
            Prefetch(
                "entry_sections__entries", Entry.objects.all().select_related("field")
            ),
        )
        .select_related("form__plotsearch__subtype__plot_search_type",)
    )
    serializer_class = AnswerSerializer
    permission_classes = (MvjDjangoModelPermissions,)
    filter_backends = (DjangoFilterBackend, AnswerInBBoxFilter)
    filterset_class = AnswerFilterSet
    bbox_filter_field = "targets__plan_unit__geometry"
    bbox_filter_include_overlapping = True

    @action(
        methods=["GET"],
        detail=True,
        serializer_class=ReadAttachmentSerializer,
        queryset=Attachment.objects.all(),
        filterset_class=None,
    )
    def attachments(self, request, pk=None):
        queryset = self.get_queryset()
        queryset = queryset.filter(answer_id=pk)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def get_permissions(self):
        if self.request.method == "POST":
            return [
                IsAuthenticated(),
            ]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == "list":
            return AnswerListSerializer
        return super().get_serializer_class()


class AttachmentViewSet(viewsets.ModelViewSet):
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.has_perm("forms.view_attachment"):
            return qs
        return qs.filter(user=self.request.user)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        queryset = queryset.filter(answer__isnull=True)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(methods=["get"], detail=True)
    def download(self, request, pk=None):
        obj = self.get_object()

        with obj.attachment.open() as fp:
            # TODO: detect file MIME type
            response = HttpResponse(File(fp), content_type="application/octet-stream")
            response["Content-Disposition"] = 'attachment; filename="{}"'.format(
                obj.attachment.name
            )

            return response


class TargetStatusViewset(
    mixins.UpdateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet
):
    queryset = TargetStatus.objects.all()
    serializer_class = TargetStatusUpdateSerializer
    permission_classes = (TargetStatusPermissions,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = TargetStatusFilterSet

    def get_serializer_class(self):
        if self.action in ("list", "metadata"):
            return TargetStatusListSerializer
        return self.serializer_class


class MeetingMemoViewset(
    mixins.CreateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet
):
    queryset = MeetingMemo.objects.all()
    serializer_class = MeetingMemoSerializer
    permission_classes = (MvjDjangoModelPermissions,)

    @action(methods=["get"], detail=True)
    def download(self, request, pk=None):
        obj = self.get_object()

        with obj.meeting_memo.open() as fp:
            # TODO: detect file MIME type
            response = HttpResponse(File(fp), content_type="application/octet-stream")
            response["Content-Disposition"] = 'attachment; filename="{}"'.format(
                obj.meeting_memo.name
            )

            return response
