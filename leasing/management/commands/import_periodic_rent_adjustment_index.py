import datetime
import json
from typing import Callable, TypedDict

import requests
from django.core.management.base import BaseCommand, CommandError
from django.utils.dateparse import parse_datetime

from leasing.models.rent import (
    IndexNumberYearly,
    OldDwellingsInHousingCompaniesPriceIndex,
)


class IndexInput(TypedDict):
    """The details we need to import an index from Tilastokeskus API."""

    name: str
    url: str
    code: str


class ColumnItem(TypedDict, total=False):
    """Details of a column in API response data.

    Based on section 4.5 in API docs https://pxdata.stat.fi/API-description_SCB.pdf

    Keys:
        code: Identifier for the column.
        text: Textual display name for the column.
        type: Type of the column: "d" = dimension, "t" = time, "c" = measure. \
              Optional. Default: "d".
        unit: Unit for the measures. Only for type "c". Optional.
        comment: Optional.
    """

    code: str
    text: str
    type: str
    unit: str
    comment: str


class CommentItem(TypedDict):
    """A single comment item for a value in API response data.

    Keys:
        variable: Identifies the column.
        value: Identifies the value.
        comment: A comment for the specified value.
    """

    variable: str
    value: str
    comment: str


class DataPoint(TypedDict):
    """A single data point from the API response data.

    All keys and values should be in same order as "columns" items in API
    response data.

    Keys:
        key: List of all dimension and time column values.
        values: List of all measure column values.
    """

    key: list[str]
    values: list[str]


class MetadataItem(TypedDict):
    """Metadata details for the database table that the response is based on."""

    updated: str
    label: str
    source: str


class ResponseData(TypedDict):
    """The entire data part of the API response."""

    columns: list[ColumnItem]
    comments: list[CommentItem]
    data: list[DataPoint]
    metadata: list[MetadataItem]


class ResponseDataError(Exception):
    """When the data from API response might cause the program to malfunction."""

    pass


# Inputs for requesting index number details from Tilastokeskus API.
# The only values necessary for the request are the `url` and `code` values.
# The keys are arbitrary, and only for internal reference in this file.
INDEXES_TO_IMPORT: list[IndexInput] = [
    {
        "name": "13mq -- Vanhojen osakeasuntojen hintaindeksi (2020=100) ja \
                kauppojen lukumäärät, vuositasolla, 2020-2023",
        "url": "https://pxdata.stat.fi:443/PxWeb/api/v1/en/StatFin/ashi/statfin_ashi_pxt_13mq.px",
        "code": "ketj_P_QA_T",
    },
]


class Command(BaseCommand):
    help = "Import the indexes related to Periodic Rent Adjustment (Tasotarkistus) \
            from Tilastokeskus database."

    def handle(self, *args, **options):
        for index_input in INDEXES_TO_IMPORT:
            self.stdout.write(f'Index: "{index_input["name"]}"')

            index_data = _get_index_data(index_input["url"], index_input["code"])
            try:
                _check_that_response_data_is_valid(index_input, index_data)
            except ResponseDataError as e:
                self.stderr.write(
                    f"Error: {e}. Skipping import of index {index_input['name']}"
                )
                continue

            index, created = _update_or_create_index(index_input, index_data)
            self.stdout.write(
                "Added new index." if created else "Updated existing index."
            )

            numbers_updated, numbers_created = _update_or_create_index_numbers(
                index_input, index_data, index
            )
            self.stdout.write(
                f"Updated {numbers_updated} and created {numbers_created} index numbers."
            )

        self.stdout.write("Done")


def _get_index_data(url: str, code: str) -> ResponseData:
    """Fetches the price index data from Tilastokeskus database.

    Example CURL command how to get the data manually:

curl -X POST "https://pxdata.stat.fi:443/PxWeb/api/v1/fi/StatFin/ashi/statfin_ashi_pxt_13mq.px" \
-d  '{
        "query": [
            {
                "code":"Alue",
                "selection":{"filter":"item","values":["pks"]}
            },
            {
                "code":"Tiedot",
                "selection":{"filter":"item","values":["ketj_P_QA_T"]}
            }
        ],
        "response":{"format":"json"}
}'

    Args:
        url: API endpoint URL.
        code: Identifier for the price index column.
    """
    filter_greater_helsinki_area = {
        "code": "Alue",
        "selection": {"filter": "item", "values": ["pks"]},
    }
    filter_price_index = {
        "code": "Tiedot",
        "selection": {"filter": "item", "values": [code]},
    }
    query = {
        "query": [filter_greater_helsinki_area, filter_price_index],
        "response": {"format": "json"},
    }
    r = requests.post(url, data=json.dumps(query))
    if r.status_code != 200:
        raise CommandError("Failed to download index")

    return r.json()


def _check_that_response_data_is_valid(
    index_input: IndexInput, index_data: ResponseData
) -> None:
    """Checks the API response data for missing data.

    Raises an error if necessary columns are missing in source table.

    Raises:
        ResponseDataError: If some necessary content is missing from API \
        response data.
    """
    columns = index_data.get("columns", [])
    try:
        _find_key_position(columns, "Vuosi")
        _find_key_position(columns, "Alue")
        _find_column_position(columns, index_input["code"])
        _find_value_position(columns, index_input["code"])
    except ResponseDataError as e:
        raise e


def _find_key_position(columns: list[ColumnItem], code: str) -> int:
    """Finds the position of a dimension or time value in the "key" list of each
    data point based on its code.

    Key columns are:
    - time (type: "t")
    - dimension (type: "d" or not specified)

    The only other column type is "c" which means a measure column.

    Args:
        columns: List of column details.
        code: Code of the key whose position we want to find.

    Raises:
        ResponseDataError if a key column with this code is not present.
    """
    return _find_column_position(
        columns, code, lambda column: "type" not in column or column["type"] != "c"
    )


def _find_value_position(columns: list[ColumnItem], code: str) -> int:
    """Finds the position of a measure value in the "values" list of each data
    point based on its code.

    Measure columns are identified with type: "c".

    Args:
        columns: List of column details.
        code: Code of the measure whose position we want to find.

    Raises:
        ResponseDataError if a value column with this code is not present.
    """
    return _find_column_position(
        columns, code, lambda column: "type" in column and column["type"] == "c"
    )


def _find_column_position(
    columns: list[ColumnItem],
    code: str,
    condition: Callable[[ColumnItem], bool] = (lambda x: True),
) -> int:
    """Finds the position of a column in the "columns" list based on its code.

    Args:
        columns: List of column details.
        code: Code of the column whose position we want to find.
        condition: A condition to only include columns based on some criterion.

    Raises:
        ResponseDataError if a column with this code matching the condition is \
        not present.
    """
    position = -1  # then the first detected value position will be 0
    for c in columns:
        if condition(c):
            position += 1
            if c["code"] == code:
                return position

    raise ResponseDataError(f'Did not find the column "{code}" in API response data')


def _update_or_create_index(
    index_input: IndexInput, index_data: ResponseData
) -> tuple[OldDwellingsInHousingCompaniesPriceIndex, bool]:
    """Updates or creates a price index based on Tilastokeskus API data."""
    columns = index_data.get("columns", [])
    index_column_pos = _find_column_position(columns, index_input["code"])
    index_column_details = columns[index_column_pos]

    table_metadata = index_data.get("metadata", [])
    metadata = table_metadata[0] if table_metadata else {}

    index, created = OldDwellingsInHousingCompaniesPriceIndex.objects.update_or_create(
        code=index_column_details.get("code", None),
        defaults={
            "url": index_input["url"],
            "name": index_column_details.get("text", ""),
            "comment": index_column_details.get("comment", ""),
            "source": metadata.get("source", ""),
            "source_table_updated": _get_update_date(metadata),
            "source_table_label": metadata.get("label", ""),
        },
    )
    return index, created


def _update_or_create_index_numbers(
    index_input: IndexInput,
    index_data: ResponseData,
    index: OldDwellingsInHousingCompaniesPriceIndex,
) -> tuple[int, int]:
    """Updates or creates the price numbers related to a price index based on
    Tilastokeskus API data.

    Returns:
        Count of updated index numbers, and count of created index numbers.
    """
    columns = index_data.get("columns", [])
    year_key_pos = _find_key_position(columns, "Vuosi")
    number_value_pos = _find_value_position(columns, index_input["code"])
    region_key_pos = _find_key_position(columns, "Alue")

    data_points = index_data.get("data", [])
    comments = index_data.get("comments", [])
    numbers_updated = 0
    numbers_created = 0

    for dp in data_points:
        year = int(dp["key"][year_key_pos])
        number = _cast_index_number_to_float_or_none(dp["values"][number_value_pos])
        region = dp["key"][region_key_pos]
        comment = _find_comment_for_value(dp, comments, columns)
        # TODO verify in 5.9. meeting: should we exclude "ennakkotieto" commented values?
        _, created = IndexNumberYearly.objects.update_or_create(
            index=index,
            year=year,
            defaults={
                "number": number,
                "region": region,
                "comment": comment,
            },
        )
        if created:
            numbers_created += 1
        else:
            numbers_updated += 1

    return (numbers_updated, numbers_created)


def _find_comment_for_value(
    data_point: DataPoint,
    comments: list[CommentItem],
    columns: list[ColumnItem],
) -> str:
    """Find a comment for the given data point, or empty string if not found.

    Args:
        data_point: The item we are searching for a comment for.
        comments: All comment items.
        columns: All column detail items, to connect the data point to a \
                possible comment.
    """
    for c in comments:
        target_column_code = c.get("variable", "")
        target_value = c.get("value", "")

        column_pos = _find_column_position(columns, target_column_code)
        if column_pos is not None:
            if data_point["key"][column_pos] == target_value:
                return c.get("comment", None)

    return ""


def _get_update_date(metadata: MetadataItem | dict) -> datetime.datetime | None:
    """Extracts the "updated" metadata string as timezone-aware datetime.

    API seems to use a datetime string format like '2024-07-26T05.00.00Z'.
    A proper ISO format datetime string would use colons instead,
    like '2024-07-26T05:00:00Z'.

    Raises:
        ValueError if the input is well formatted but not a valid datetime.

    Returns:
        Datetime, or None if the metadata doesn't contain a well-formatted \
        datetime string.
    """
    update_time_str: str = metadata.get("updated", "")
    proper_iso_str = update_time_str.replace(
        ".", ":"
    )  # Assumes no sub-second values such as "T05:00:00.000" in the string.
    return parse_datetime(proper_iso_str)


def _cast_index_number_to_float_or_none(number_str: str) -> float | None:
    """Casts the number from string to float, or None if ".".

    Tilastokeskus API substitutes missing index numbers with the period
    character (".").
    """
    if number_str == ".":
        return None
    else:
        return float(number_str)
