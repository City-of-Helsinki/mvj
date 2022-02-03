from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, viewsets
from rest_framework.response import Response

from forms.models import Answer, Form
from forms.serializers.form import AnswerSerializer, FormSerializer
from leasing.permissions import MvjDjangoModelPermissionsOrAnonReadOnly


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
    queryset = Answer.objects.all()
    serializer_class = AnswerSerializer

    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        entries = dict(dict())
        for entry in instance.entries.all():
            entries[entry.field.section.section_identifier][entry.field.field_identifier] = entry.value
        serializer = self.get_serializer({"form": instance.form, "user": instance.user, "entries": entries, "ready": instance.ready})
        return Response(serializer.data)
