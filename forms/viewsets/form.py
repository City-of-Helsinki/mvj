from rest_framework import viewsets

from forms.models import Form
from forms.serializers.form import FormSerializer


class FormViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Form.objects.all()
    serializer_class = FormSerializer
