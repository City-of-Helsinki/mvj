from enum import Enum

from xlsxwriter.utility import xl_range, xl_rowcol_to_cell


class FormatType(Enum):
    BOLD = 'bold'
    DATE = 'date'
    MONEY = 'money'
    BOLD_MONEY = 'bold_money'


class ExcelRow:
    def __init__(self, cells=None):
        self.cells = []

        if cells is not None:
            self.cells.extend(cells)


class ExcelCell:
    def __init__(self, column, value=None, format_type=None):
        self.column = column
        self.value = value
        self.format_type = format_type
        self.row = None
        self.first_data_row_num = None

    def get_value(self):
        return self.value

    def get_format_type(self):
        return self.format_type

    def set_row(self, row_num):
        self.row = row_num

    def set_first_data_row_num(self, row_num):
        self.first_data_row_num = row_num


class PreviousRowsSumCell(ExcelCell):
    def __init__(self, column, count, format_type=FormatType.BOLD):
        super().__init__(column, format_type=format_type)

        self.count = count

    def get_value(self):
        return '=SUM({}:{})'.format(
            xl_rowcol_to_cell(self.row - self.count, self.column),
            xl_rowcol_to_cell(self.row - 1, self.column),
        )


class SumCell(ExcelCell):
    def __init__(self, column, format_type=FormatType.BOLD, target_ranges=None):
        super().__init__(column, format_type=format_type)

        if target_ranges:
            self.target_ranges = target_ranges
        else:
            self.target_ranges = []

    def add_target_range(self, range):
        self.target_ranges.append(range)

    def get_value(self):
        return '=SUM({})'.format(','.join([xl_range(
            i[0] + self.first_data_row_num, i[1],
            i[2] + self.first_data_row_num, i[3]
        ) for i in self.target_ranges]))
