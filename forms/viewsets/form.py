from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, viewsets

from forms.models import Answer, Field, Form, Section
from forms.serializers.form import (
    AnswerSerializer,
    FieldSerializer,
    FormSerializer,
    SectionSerializer,
)


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
    queryset = Form.objects.all().prefetch_related("sections")
    serializer_class = FormSerializer


class AnswerViewSet(viewsets.ModelViewSet):
    queryset = Answer.objects.all()
    serializer_class = AnswerSerializer


class SectionViewSet(viewsets.ModelViewSet):
    queryset = Section.objects.all()
    serializer_class = SectionSerializer


class FieldViewSet(viewsets.ModelViewSet):
    queryset = Field.objects.all()
    serializer_class = FieldSerializer
