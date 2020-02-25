from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from leasing.report.forms import ReportFormBase
from leasing.report.serializers import ReportOutputSerializer


class ReportBase:
    name = None
    slug = None
    input_fields = {}
    output_fields = {}

    def __init__(self):
        self.form = None

    def get_form(self, data=None):
        self.form = ReportFormBase(data, input_fields=self.input_fields)

        return self.form

    def get_response(self, request):
        input_form = self.get_form(request.query_params)

        if not input_form.is_valid():
            raise ValidationError({'detail': input_form.errors})

        qs = self.get_data(input_form.cleaned_data)

        serializer_class = self.get_serializer_class()
        serializer = serializer_class(qs, output_fields=self.output_fields, many=True)

        return Response(serializer.data)

    def get_serializer_class(self):
        return ReportOutputSerializer

    def get_filename(self, format):
        return '{}_{}.{}'.format(timezone.now().strftime('%Y-%m-%d_%H-%M'), self.slug, format)

    def get_field_attr(self, field_name, attr_name, default=None):
        value = default
        if field_name in self.output_fields and attr_name in self.output_fields[field_name]:
            value = self.output_fields[field_name][attr_name]

        return value
