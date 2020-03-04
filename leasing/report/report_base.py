from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from leasing.report.forms import ReportFormBase
from leasing.report.serializers import ReportOutputSerializer


class ReportBase:
    # Name is returned in the report list and in the metadata
    name = None

    # Description is returned in the report list and in the metadata
    description = None

    # Slug is the id of the report
    slug = None

    # Input fields are form fields that are used to validate the input
    # parameters. The form's validated_data is passed to get_data function.
    input_fields = {}

    # Output fields are used to set the fields in the output serializer.
    #
    # The format is
    #  'field_name': {
    #      'label': '',
    #      'source: '',
    #      'serializer_field': None,
    #      'width': None,
    #      'format': '',
    #   },
    #
    # label is returned in the metadata
    #
    # source is kind of same as in serializers. Source doesn't need to be
    #   defined if the "field_name" is the same as in the data. Alternatively
    #   the source can be a callable (callable receives the current object as a
    #   parameter) or a string (in which case the value is the name of the
    #   desired attribute)
    #
    # serializer_field is optionally an instantiated serializer field. By default
    #   the serializer field is a ReadOnlyField (or SerializerMethodField if
    #   the source is a callable). e.g. serializer_field should be set when the
    #   field is an enum:
    #     'state': {
    #         'label': _('State'),
    #         'serializer_field': EnumField(enum=InvoiceState)
    #     },
    #
    # width and format are used in modify the output of the XLSX renderer.
    # width sets the column width and format sets the cell format. Possible
    # format values are "date", "money" or "boolean". Any other value leaves
    # the formatting to xlsxwriter.
    output_fields = {}

    def __init__(self):
        self.form = None

    def get_form(self, data=None):
        """Initializes a form with fields from input_fields, saves the form as
        self.form instance attribute and returns it."""
        self.form = ReportFormBase(data, input_fields=self.input_fields)

        return self.form

    def get_input_data(self, request):
        """Validates the request's query parameters using self.form"""
        input_form = self.get_form(request.query_params)

        if not input_form.is_valid():
            raise ValidationError({'detail': input_form.errors})

        return input_form.cleaned_data

    def serialize_data(self, report_data):
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(report_data, output_fields=self.output_fields, many=True)

        return serializer.data

    def get_response(self, request):
        report_data = self.get_data(self.get_input_data(request))
        serialized_report_data = self.serialize_data(report_data)

        return Response(serialized_report_data)

    def get_serializer_class(self):
        return ReportOutputSerializer

    def get_filename(self, format):
        return '{}_{}.{}'.format(timezone.now().strftime('%Y-%m-%d_%H-%M'), self.slug, format)

    def get_output_field_attr(self, field_name, attr_name, default=None):
        """Returns the value of [`field_name`][`attr_name`] attribute from output_fields"""
        value = default
        if field_name in self.output_fields and attr_name in self.output_fields[field_name]:
            value = self.output_fields[field_name][attr_name]

        return value
