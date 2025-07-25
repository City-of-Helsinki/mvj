from io import BytesIO
from typing import Any, Type, Union

import xlsxwriter
from django.conf import settings
from django.core.mail import EmailMessage
from django.db.models import Model, QuerySet
from django.forms.models import ModelChoiceIteratorValue
from django.utils import timezone
from django.utils.functional import Promise
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _
from django_q.conf import Conf
from django_q.tasks import async_task
from rest_framework.exceptions import ValidationError
from rest_framework.fields import ChoiceField
from rest_framework.request import Request
from rest_framework.response import Response

from leasing.report.excel import ExcelRow, FormatType
from leasing.report.forms import ReportFormBase
from leasing.report.lease.common_getters import (
    get_identifier_string_from_lease_link_data,
)
from leasing.report.serializers import ReportOutputSerializer


class ReportBase:
    # Name is returned in the report list and in the metadata
    name: Union[str, Promise, None] = None

    # Description is returned in the report list and in the metadata
    description: Union[str, Promise, None] = None

    # Slug is the id of the report
    slug: Union[str, None] = None

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
    #      'is_numeric': False,
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
    # format values are "bold", "date", "money", "bold_money", "percentage",
    # "boolean", and "area". Any other value leaves the formatting to xlsxwriter.
    # (The percentage format divides the value by 100 when exporting to Excel)
    #
    # is_numeric only viewed in the output metadata. The field can be used
    # in the UI to allow easier ordering of the data.
    output_fields = {}

    # If the column labels should be automatically added as the first row
    automatic_excel_column_labels = True

    # The query form model of report
    form = None

    # Is the data already sorted in the backend? i.e. the UI shouldn't order the data.
    # This is exposed in the report metadata in the key "is_already_sorted".
    is_already_sorted = False

    @classmethod
    def get_output_fields_metadata(cls):
        metadata = {}
        for field_name, output_field in cls.output_fields.items():
            metadata[field_name] = {
                k: v
                for k, v in output_field.items()
                if k not in ["source", "width", "serializer_field"]
            }
            if output_field.get("is_numeric") is None:
                is_numeric = False
                if output_field.get("format") in [
                    "money",
                    "bold_money",
                    "percentage",
                    "area",
                ]:
                    is_numeric = True
                metadata[field_name]["is_numeric"] = is_numeric

            serializer_field = output_field.get("serializer_field")
            if serializer_field and hasattr(serializer_field, "choices"):
                choices = []
                for choice_value, choice_label in serializer_field.choices.items():
                    choices.append(
                        {
                            "value": (
                                choice_value.value
                                if isinstance(choice_value, ModelChoiceIteratorValue)
                                else choice_value
                            ),
                            "display_name": choice_label,
                        }
                    )

                metadata[field_name]["choices"] = choices

        return metadata

    def set_form(self, data=None):
        """Initializes a form with fields from input_fields, saves the form as
        self.form instance attribute and returns it."""
        report_form = ReportFormBase(data, input_fields=self.input_fields)
        self.form = report_form
        return report_form

    def get_input_data(self, query_params: dict[str, str]):
        """Validates the request's query parameters using self.form"""
        input_form = self.set_form(query_params)

        if not input_form.is_valid():
            raise ValidationError({"detail": input_form.errors})

        return input_form.cleaned_data

    def serialize_data(self, report_data):
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(
            report_data, output_fields=self.output_fields, many=True
        )
        return serializer.data

    def get_response(self, request: Request) -> Response:
        input_data = self.get_input_data(request.query_params)
        report_data = self.get_data(input_data)
        serialized_report_data = self.serialize_data(report_data)
        return Response(serialized_report_data)

    def get_data(self, input_data: dict[str, Any]) -> list[dict] | QuerySet:
        raise NotImplementedError(
            "Please implement this method in the concrete report class"
        )

    def get_serializer_class(self) -> Type[ReportOutputSerializer]:
        return ReportOutputSerializer

    def get_filename(self, file_format: str):
        return "{}_{}.{}".format(
            timezone.localtime(timezone.now()).strftime("%Y-%m-%d_%H-%M"),
            self.slug,
            file_format,
        )

    def get_output_field_attr(self, field_name, attr_name, default=None):
        """Returns the value of [`field_name`][`attr_name`] attribute from output_fields"""
        value = default
        if (
            field_name in self.output_fields
            and attr_name in self.output_fields[field_name]
        ):
            value = self.output_fields[field_name][attr_name]

        return value

    def data_as_excel(self, data: list[dict | ExcelRow]):
        report = self

        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet()

        formats = {
            FormatType.BOLD: workbook.add_format({"bold": True}),
            FormatType.DATE: workbook.add_format({"num_format": "dd.mm.yyyy"}),
            FormatType.MONEY: workbook.add_format({"num_format": "#,##0.00 €"}),
            FormatType.BOLD_MONEY: workbook.add_format(
                {"bold": True, "num_format": "#,##0.00 €"}
            ),
            FormatType.PERCENTAGE: workbook.add_format({"num_format": "0.0 %"}),
            FormatType.AREA: workbook.add_format({"num_format": r"#,##0.00 \m\²"}),
        }

        row_num = 0

        # On the first row print the report name
        worksheet.write(row_num, 0, str(report.name), formats[FormatType.BOLD])

        # On the second row print the report description
        row_num += 1
        worksheet.write(row_num, 0, str(report.description))

        # On the fourth row forwards print the input fields and their values
        row_num += 2
        row_num = self.write_input_field_value_rows(
            worksheet, report.form, row_num, formats
        )

        # Set column widths
        for index, field_name in enumerate(report.output_fields.keys()):
            worksheet.set_column(
                index,
                index,
                report.get_output_field_attr(field_name, "width", default=10),
            )

        # Labels from the first non-ExcelRow row
        if report.automatic_excel_column_labels:
            row_num += 1

            lookup_row_num = 0
            while lookup_row_num < len(data) and isinstance(
                data[lookup_row_num], ExcelRow
            ):
                lookup_row_num += 1

            if len(data) > lookup_row_num:
                for index, field_name in enumerate(data[lookup_row_num].keys()):
                    field_label = report.get_output_field_attr(
                        field_name, "label", default=field_name
                    )

                    worksheet.write(
                        row_num, index, str(field_label), formats[FormatType.BOLD]
                    )

        # The data itself
        row_num += 1
        first_data_row_num = row_num
        for row in data:
            if isinstance(row, dict):
                row["lease_identifier"] = get_identifier_string_from_lease_link_data(
                    row
                )
                self.write_dict_row_to_worksheet(worksheet, formats, row_num, row)
            elif isinstance(row, ExcelRow):
                for cell in row.cells:
                    cell.set_row(row_num)
                    cell.set_first_data_row_num(first_data_row_num)
                    worksheet.write(
                        row_num,
                        cell.column,
                        cell.get_value(),
                        (
                            formats[cell.get_format_type()]
                            if cell.get_format_type() in formats
                            else None
                        ),
                    )

            row_num += 1

        workbook.close()

        return output.getvalue()

    def write_dict_row_to_worksheet(self, worksheet, formats, row_num, row):
        """
        Writes row on worksheet on given row number from dict with relevant formatting.
        """
        column = 0
        for field_name, field_value in row.items():
            field_format = None

            field_format_name = self.get_output_field_attr(field_name, "format")

            match field_format_name:
                case "date":
                    field_format = formats[FormatType.DATE]
                case "percentage":
                    field_format = formats[FormatType.PERCENTAGE]
                    if field_value:
                        try:
                            field_value = field_value / 100
                        except TypeError:
                            field_value = 0
                case "money":
                    if field_value != 0:
                        field_format = formats[FormatType.MONEY]
                case "boolean":
                    if field_value:
                        field_value = str(_("Yes"))
                    else:
                        field_value = str(_("No"))
                case "area":
                    field_format = formats[FormatType.AREA]

            field_serializer_field = self.get_output_field_attr(
                field_name, "serializer_field"
            )
            if isinstance(field_serializer_field, ChoiceField):
                field_value = (
                    str(field_serializer_field.choices.get(field_value))
                    if field_value
                    else ""
                )

            worksheet.write(row_num, column, field_value, field_format)
            column += 1

    def write_input_field_value_rows(
        self, worksheet, report_form, row_num_cursor, formats
    ):
        """
        Writes form input values from report form onto given worksheet at given row number. Requires formats as well.
        Returns new row num at end of row data written by function.
        """
        for input_field_name, input_field in report_form.fields.items():
            worksheet.write(
                row_num_cursor,
                0,
                "{}:".format(input_field.label),
                formats[FormatType.BOLD],
            )
            field_format = None
            if input_field.__class__.__name__ == "DateField":
                field_format = formats[FormatType.DATE]

            input_value = report_form.cleaned_data[input_field_name]
            if hasattr(input_field, "choices"):
                for choice_value, choice_label in input_field.choices:
                    if choice_value == input_value:
                        input_value = str(choice_label)
                        break

            if isinstance(input_value, Model):
                input_value = str(input_value)

            if isinstance(input_value, bool):
                if input_value:
                    input_value = gettext("Yes")
                else:
                    input_value = gettext("No")

            if isinstance(input_value, QuerySet):
                input_value = ", ".join([str(v) for v in input_value.all()])

            worksheet.write(row_num_cursor, 1, input_value, field_format)
            row_num_cursor += 1

        return row_num_cursor


class AsyncReportBase(ReportBase):

    @classmethod
    def get_output_fields_metadata(cls):
        return {"message": {"label": _("Message")}}

    def get_response(self, request: Request) -> Response:
        user_email: str = request.user.email
        async_task(
            generate_email_report,
            email=user_email,
            query_params=request.query_params,
            report_class=self.__class__,
            hook=send_email_report,
            timeout=getattr(self, "async_task_timeout", Conf.TIMEOUT),
        )

        return Response(
            {"message": _("Results will be sent by email to {}").format(user_email)}
        )


def generate_email_report(
    email: str,
    query_params: dict[str, str],
    report_class: Type[AsyncReportBase],
) -> dict[str, Any]:
    """Generates the report based on the selected report settings."""
    del email  # Unused in this function, but needed in the hook

    report = report_class()
    input_data = report.get_input_data(query_params)
    report_data = report.get_data(input_data)

    if isinstance(report_data, list):
        spreadsheet = report.data_as_excel(report_data)
    else:
        serialized_data = report.serialize_data(report_data)
        spreadsheet = report.data_as_excel(serialized_data)

    return {
        "report_spreadsheet": spreadsheet,
        "report_name": report.name,
        "report_filename": report.get_filename("xlsx"),
    }


def send_email_report(task):
    email = task.kwargs["email"]
    report_name = task.result["report_name"]
    report_filename = task.result["report_filename"]
    report_spreadsheet = task.result["report_spreadsheet"]

    message = EmailMessage(from_email=settings.MVJ_EMAIL_FROM, to=[email])

    if task.success:
        message.subject = _('Report "{}" successfully generated').format(report_name)
        message.body = _("Generated report attached")
        message.attach(
            report_filename,
            report_spreadsheet,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    else:
        message.subject = _('Failed to generate report "{}"').format(report_name)
        message.body = _("Please try again")

    message.send()
