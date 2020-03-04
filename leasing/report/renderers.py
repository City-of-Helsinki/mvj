import json
from collections import OrderedDict
from io import BytesIO

import xlsxwriter
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Model
from django.utils.translation import ugettext as _
from rest_framework import renderers

from leasing.report.excel import ExcelRow


class XLSXRenderer(renderers.BaseRenderer):
    media_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    format = 'xlsx'
    charset = 'utf-8'
    render_style = 'binary'

    def render(self, data, media_type=None, renderer_context=None):  # NOQA C901 'XLSXRenderer.render' is too complex
        # Return JSON response if the view is not a report or when an error occurred
        if renderer_context['view'].action != 'retrieve' or renderer_context['response'].status_code != 200:
            renderer_context['response']['Content-Type'] = 'application/json'
            return json.dumps(data, cls=DjangoJSONEncoder)

        report = renderer_context['view'].report

        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet()

        bold_format = workbook.add_format({'bold': True})
        date_format = workbook.add_format({'num_format': 'dd.mm.yyyy'})
        money_format = workbook.add_format({'num_format': '€#.##'})

        row_num = 0

        # On the first row print the report name
        worksheet.write(row_num, 0, str(report.name), bold_format)

        # On the second row print the report description
        row_num += 1
        worksheet.write(row_num, 0, str(report.description))

        # On the fourth row forwards print the input fields and their values
        row_num += 2
        for input_field_name, input_field in report.form.fields.items():
            worksheet.write(row_num, 0, '{}:'.format(input_field.label), bold_format)
            field_format = None
            if input_field.__class__.__name__ == 'DateField':
                field_format = date_format

            input_value = report.form.cleaned_data[input_field_name]
            if hasattr(input_field, 'choices'):
                for choice_value, choice_label in input_field.choices:
                    if choice_value == input_value:
                        input_value = str(choice_label)
                        break

            if isinstance(input_value, Model):
                input_value = str(input_value)

            worksheet.write(row_num, 1, input_value, field_format)
            row_num += 1

        # Labels from the first row
        row_num += 1
        for index, field_name in enumerate(data[0].keys()):
            field_label = report.get_output_field_attr(field_name, 'label', default=field_name)

            worksheet.write(row_num, index, str(field_label), bold_format)

            # Set column width
            worksheet.set_column(index, index, report.get_output_field_attr(field_name, 'width', default=10))

        # The data itself
        row_num += 1
        first_data_row_num = row_num
        for row in data:
            if isinstance(row, OrderedDict):
                column = 0
                for field_name, field_value in row.items():
                    field_format = None

                    field_format_name = report.get_output_field_attr(field_name, 'format')

                    if field_format_name == 'date':
                        field_format = date_format
                    elif field_format_name == 'money':
                        if field_value != 0:
                            field_format = money_format
                    elif field_format_name == 'boolean':
                        if field_value:
                            field_value = _('Yes')
                        else:
                            field_value = _('No')

                    worksheet.write(row_num, column, field_value, field_format)
                    column += 1
            elif isinstance(row, ExcelRow):
                for cell in row.cells:
                    cell.set_row(row_num)
                    cell.set_first_data_row_num(first_data_row_num)
                    worksheet.write(row_num, cell.column, cell.get_value(), cell.get_format())

            row_num += 1

        workbook.close()

        return output.getvalue()
