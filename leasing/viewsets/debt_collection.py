from rest_framework.decorators import action

from field_permissions.viewsets import FieldPermissionsViewsetMixin
from file_operations.viewsets.mixins import FileMixin
from leasing.filters import (
    CollectionCourtDecisionFilter,
    CollectionLetterFilter,
    CollectionNoteFilter,
)
from leasing.models.debt_collection import (
    CollectionCourtDecision,
    CollectionLetter,
    CollectionLetterTemplate,
    CollectionNote,
)
from leasing.serializers.debt_collection import (
    CollectionCourtDecisionCreateUpdateSerializer,
    CollectionCourtDecisionSerializer,
    CollectionLetterCreateUpdateSerializer,
    CollectionLetterSerializer,
    CollectionLetterTemplateSerializer,
    CollectionNoteCreateUpdateSerializer,
    CollectionNoteSerializer,
)
from leasing.viewsets.utils import AtomicTransactionModelViewSet, MultiPartJsonParser


class CollectionCourtDecisionViewSet(
    FileMixin,
    FieldPermissionsViewsetMixin,
    AtomicTransactionModelViewSet,
):
    queryset = CollectionCourtDecision.objects.all()
    serializer_class = CollectionCourtDecisionSerializer
    parser_classes = (MultiPartJsonParser,)
    filterset_class = CollectionCourtDecisionFilter

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update", "metadata"):
            return CollectionCourtDecisionCreateUpdateSerializer

        return CollectionCourtDecisionSerializer

    @action(methods=["get"], detail=True)
    def download(self, request, pk=None):
        """Needed to inform FileDownloadMixin of which field holds the file."""
        return super().download(request, pk, file_field="file")


class CollectionLetterViewSet(
    FileMixin,
    FieldPermissionsViewsetMixin,
    AtomicTransactionModelViewSet,
):
    queryset = CollectionLetter.objects.all()
    serializer_class = CollectionLetterSerializer
    parser_classes = (MultiPartJsonParser,)
    filterset_class = CollectionLetterFilter

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update", "metadata"):
            return CollectionLetterCreateUpdateSerializer

        return CollectionLetterSerializer

    @action(methods=["get"], detail=True)
    def download(self, request, pk=None):
        """Needed to inform FileDownloadMixin of which field holds the file."""
        return super().download(request, pk, file_field="file")


class CollectionLetterTemplateViewSet(AtomicTransactionModelViewSet):
    queryset = CollectionLetterTemplate.objects.all()
    serializer_class = CollectionLetterTemplateSerializer


class CollectionNoteViewSet(
    FieldPermissionsViewsetMixin, AtomicTransactionModelViewSet
):
    queryset = CollectionNote.objects.all().select_related("user")
    serializer_class = CollectionNoteSerializer
    filterset_class = CollectionNoteFilter

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update", "metadata"):
            return CollectionNoteCreateUpdateSerializer

        return CollectionNoteSerializer
