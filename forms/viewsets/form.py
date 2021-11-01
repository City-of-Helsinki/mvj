from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, viewsets

from forms.models import Answer, Form
from forms.serializers.form import AnswerSerializer, FormSerializer


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

    def get_queryset(self):
        queryset = Form.objects.all().prefetch_related("sections")
        return queryset


class AnswerViewSet(viewsets.ModelViewSet):
    queryset = Answer.objects.all()
    serializer_class = AnswerSerializer
