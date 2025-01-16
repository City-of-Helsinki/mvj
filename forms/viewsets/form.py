from django.db.models import Prefetch
from django.utils.translation import get_language_from_request
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from forms.filter import AnswerFilterSet, TargetStatusFilterSet
from forms.models import Answer, Entry, Form
from forms.models.form import AnswerOpeningRecord, Attachment
from forms.permissions import (
    AnswerPermissions,
    AttachmentPermissions,
    OpeningRecordPermissions,
    TargetStatusPermissions,
)
from forms.serializers.form import (
    AnswerListSerializer,
    AnswerOpeningRecordSerializer,
    AnswerPublicSerializer,
    AnswerSerializer,
    AttachmentSerializer,
    FormSerializer,
    MeetingMemoSerializer,
    ReadAttachmentSerializer,
    TargetStatusListSerializer,
    TargetStatusUpdateSerializer,
)
from forms.utils import AnswerInBBoxFilter, handle_email_sending
from leasing.permissions import MvjDjangoModelPermissions
from plotsearch.models import TargetStatus
from plotsearch.models.plot_search import MeetingMemo
from utils.viewsets.mixins import FileDownloadMixin, FileExtensionFileMixin


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
    permission_classes = (MvjDjangoModelPermissions,)

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
        Answer.objects.filter(area_search__isnull=True)
        .prefetch_related(
            "entry_sections",
            "targets",
            "statuses",
            Prefetch(
                "entry_sections__entries", Entry.objects.all().select_related("field")
            ),
        )
        .select_related(
            "form__plotsearch__subtype__plot_search_type",
        )
    )
    serializer_class = AnswerSerializer
    permission_classes = (AnswerPermissions,)
    perms_map = {
        "GET": ["forms.view_answer"],
        "HEAD": ["forms.view_answer"],
        "PUT": ["forms.change_answer"],
        "PATCH": ["forms.change_answer"],
        "DELETE": ["forms.delete_answer"],
    }
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

    def get_queryset(self):
        if self.action == "retrieve":
            return Answer.objects.all()
        return super().get_queryset()

    def get_serializer_class(self):
        if self.action == "list":
            return AnswerListSerializer
        return super().get_serializer_class()


class AnswerPublicViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """Public API for submitting form answers with added restrictions."""

    http_method_names = ["post", "options"]  # In public API, only POST is allowed
    serializer_class = AnswerPublicSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = None
    filterset_class = None

    def get_queryset(self):
        return Answer.objects.none()

    def get_permissions(self):
        if self.request.method in ["POST", "OPTIONS"]:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = []

        return [permission() for permission in permission_classes]

    def create(self, request, *args, **kwargs):
        user_language = get_language_from_request(request)
        response = super().create(request, *args, **kwargs)
        handle_email_sending(response, user_language)
        return response


class AttachmentViewSet(FileDownloadMixin, viewsets.ModelViewSet):
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer
    permission_classes = (AttachmentPermissions,)
    perms_map = {
        "GET": ["forms.view_attachment"],
        "HEAD": ["forms.view_attachment"],
        "PUT": ["forms.change_attachment"],
        "PATCH": ["forms.change_attachment"],
        "DELETE": ["forms.delete_attachment"],
    }

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
        return super().download(request, pk, file_field="attachment")


class AttachmentPublicViewSet(FileExtensionFileMixin, AttachmentViewSet):
    """Includes FileExtensionFileMixin to validate file extensions."""

    pass


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
    FileDownloadMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    queryset = MeetingMemo.objects.all()
    serializer_class = MeetingMemoSerializer
    permission_classes = (MvjDjangoModelPermissions,)


class AnswerOpeningRecordViewset(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = AnswerOpeningRecord.objects.all()
    serializer_class = AnswerOpeningRecordSerializer
    permission_classes = (OpeningRecordPermissions,)
    perms_map = {
        "GET": ["forms.view_answeropeningrecord"],
        "HEAD": ["forms.view_answeropeningrecord"],
        "PUT": ["forms.change_answeropeningrecord"],
        "PATCH": ["forms.change_answeropeningrecord"],
        "DELETE": ["forms.delete_answeropeningrecord"],
        "POST": ["forms.add_answeropeningrecord"],
    }

    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    def get_object(self):
        return super().get_object()
