from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets

from forms.models import Answer, Form
from forms.serializers.form import AnswerSerializer, FormSerializer


class FormViewSet(viewsets.ReadOnlyModelViewSet):
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["is_template"]
    queryset = Form.objects.all()
    serializer_class = FormSerializer


class AnswerViewSet(viewsets.ModelViewSet):
    queryset = Answer.objects.all()
    serializer_class = AnswerSerializer
