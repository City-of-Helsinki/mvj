from enum import Enum
from typing import TypeAlias

from xlsxwriter.utility import xl_range, xl_rowcol_to_cell


class FormatType(Enum):
    BOLD = "bold"
    BOOLEAN = "boolean"
    DATE = "date"
    MONEY = "money"
    BOLD_MONEY = "bold_money"
    PERCENTAGE = "percentage"
    AREA = "area"
    URL = "url"


class ExcelCell:
    def __init__(
        self,
        column: int,
        value: str | None = None,
        format_type: FormatType | None = None,
    ):
        self.column = column
        self.value = value
        self.format_type = format_type
        self.row: int | None = None
        self.first_data_row_num: int | None = None

    def get_value(self) -> str | None:
        return self.value

    def get_format_type(self) -> FormatType | None:
        return self.format_type

    def set_row(self, row_num: int) -> None:
        self.row = row_num

    def set_first_data_row_num(self, row_num: int) -> None:
        self.first_data_row_num = row_num


class ExcelRow:
    def __init__(self, cells: list[ExcelCell] | None = None):
        self.cells: list[ExcelCell] = []

        if cells is not None:
            self.cells.extend(cells)


class PreviousRowsSumCell(ExcelCell):
    def __init__(
        self, column: int, count: int, format_type: FormatType | None = FormatType.BOLD
    ):
        super().__init__(column, format_type=format_type)

        self.count = count

    def get_value(self) -> str:
        return "=SUM({}:{})".format(
            xl_rowcol_to_cell(self.row - self.count, self.column),
            xl_rowcol_to_cell(self.row - 1, self.column),
        )


TargetRange: TypeAlias = tuple[int, int, int, int]


class SumCell(ExcelCell):
    def __init__(
        self,
        column: int,
        format_type=FormatType.BOLD,
        target_ranges: list[TargetRange] | None = None,
    ):
        super().__init__(column, format_type=format_type)

        if target_ranges:
            self.target_ranges = target_ranges
        else:
            self.target_ranges = []

    def add_target_range(self, range: TargetRange):
        self.target_ranges.append(range)

    def get_value(self) -> str:
        return "=SUM({})".format(
            ",".join(
                [
                    xl_range(
                        i[0] + self.first_data_row_num,
                        i[1],
                        i[2] + self.first_data_row_num,
                        i[3],
                    )
                    for i in self.target_ranges
                ]
            )
        )
