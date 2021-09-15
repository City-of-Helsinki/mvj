from rest_framework import viewsets

from forms.models import Answer, Form
from forms.serializers.form import AnswerSerializer, FormSerializer


class FormViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Form.objects.all()
    serializer_class = FormSerializer


class AnswerViewSet(viewsets.ModelViewSet):
    queryset = Answer.objects.all()
    serializer_class = AnswerSerializer
