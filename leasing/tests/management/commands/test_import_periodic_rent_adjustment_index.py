import json
from copy import deepcopy
from datetime import datetime, timezone
from typing import cast

import pytest

from leasing.management.commands.import_periodic_rent_adjustment_index import (
    ColumnItem,
    CommentItem,
    DataPoint,
    IndexInput,
    MetadataItem,
    ResponseData,
    ResponseDataError,
    _cast_index_number_to_float_or_none,
    _check_that_response_data_is_valid,
    _find_comment_for_value,
    _find_key_position,
    _find_value_position,
    _get_update_date,
    _update_or_create_index,
    _update_or_create_index_numbers,
)


def test_response_data_is_valid(
    real_input_data: IndexInput,
    real_data: ResponseData,
):
    """Happy path with valid data: no exception is raised."""
    try:
        _check_that_response_data_is_valid(real_input_data, real_data)
    except ResponseDataError as e:
        pytest.fail(f"An error was raised for valid data: {e}")


def test_missing_column_raises(real_input_data: IndexInput, real_data: ResponseData):
    """Unhappy path: columns missing from the response.
    :
        Unclear whether this kind of response is possible, but if such happens it
        should raise an error.
    """
    real_data["columns"] = {}  # type: ignore
    with pytest.raises(ResponseDataError):
        _check_that_response_data_is_valid(real_input_data, real_data)


def test_key_position_found(columns_real_data: list[ColumnItem]):
    """Happy path: key positions are correctly identified in the data."""
    assert _find_key_position(columns_real_data, "Vuosi") == 0
    assert _find_key_position(columns_real_data, "Alue") == 1


def test_key_column_missing_code_raises(
    columns_real_data: list[ColumnItem],
):
    """Unhappy path: the key column cannot be found because the column code doesn't match."""
    columns = deepcopy(columns_real_data)
    for column in columns:
        column["code"] = "Something else"

    with pytest.raises(ResponseDataError):
        _find_key_position(columns, "Vuosi")


def test_key_column_wrong_type_raises(
    columns_real_data: list[ColumnItem],
):
    """Unhappy path: the key column cannot be found because the column type doesn't match."""
    columns = deepcopy(columns_real_data)
    for column in columns:
        # type c indicates a measure column instead of a key column
        column["type"] = "c"

    with pytest.raises(ResponseDataError):
        _find_key_position(columns, "Vuosineljännes")


def test_value_position_found(
    real_input_data: IndexInput,
    columns_real_data: list[ColumnItem],
):
    """Happy path: value positions are correctly identified in the data."""
    index_code = real_input_data["code"]
    assert _find_value_position(columns_real_data, index_code) == 0


def test_comment_found(
    datapoints_real_data: list[DataPoint],
    columns_real_data: list[ColumnItem],
    comments_test_data: list[CommentItem],
):
    """Happy path: a comment is properly matched to a data point."""
    dp_with_comment = datapoints_real_data[-1]
    assert (
        _find_comment_for_value(
            dp_with_comment,
            comments_test_data,
            columns_real_data,
        )
        == comments_test_data[-1]["comment"]
    )


def test_comment_not_found(
    datapoints_real_data: list[DataPoint],
    comments_test_data: list[CommentItem],
    columns_real_data: list[ColumnItem],
):
    """Happy path: a comment is not matched to non-matching data point."""
    dp_without_comment = datapoints_real_data[0]
    assert (
        _find_comment_for_value(
            dp_without_comment,
            comments_test_data,
            columns_real_data,
        )
        == ""
    )


def test_get_update_date_valid(metadata_real_data: list[MetadataItem]):
    """Happy path: update datetime is properly extracted from a string."""
    metadata = metadata_real_data[0]
    assert _get_update_date(metadata) == datetime(
        2024, 5, 3, 5, 0, 0, tzinfo=timezone.utc
    )


@pytest.mark.parametrize(
    "index_number, expected",
    [("100.00", 100.00), ("0", 0), ("123456.1234", 123456.1234), (".", None)],
)
def test_cast_index_number_to_float_or_none(index_number: str, expected: int | None):
    """Happy path: index number is a proper number that can be cast to float,
    while period character "." is cast to None."""
    assert _cast_index_number_to_float_or_none(index_number) == expected


@pytest.mark.django_db
def test_create_or_update_index():
    """Happy path: a new index is saved to DB with correct column values,
    and is updated when using the same index code.
    """
    creation_input = cast(
        IndexInput,
        {
            "name": "",
            "url": "https://test.url.1",
            "code": "test_index_code_1",
        },
    )
    creation_data = cast(
        ResponseData,
        {
            "columns": [
                {
                    "code": "test_index_code_1",
                    "text": "Test column text 1",
                    "comment": "Test column comment 1",
                    "type": "c",
                }
            ],
            "comments": [],
            "data": [],
            "metadata": [
                {
                    "label": "Test source table label 1",
                    "source": "Test data source 1",
                    "updated": "2024-01-01T05.00.00Z",
                }
            ],
        },
    )
    # Case 1: Create new index row
    created_index, created = _update_or_create_index(creation_input, creation_data)
    assert created is True
    assert created_index.code == "test_index_code_1"
    assert created_index.url == "https://test.url.1"
    assert created_index.name == "Test column text 1"
    assert created_index.comment == "Test column comment 1"
    assert created_index.source == "Test data source 1"
    assert created_index.source_table_updated == datetime(
        year=2024, month=1, day=1, hour=5, tzinfo=timezone.utc
    )
    assert created_index.source_table_label == "Test source table label 1"

    # Case 2: Update existing index row

    # Increment test values from 1 to 2 to use in the update
    json_str = json.dumps({"input": creation_input, "data": creation_data})
    incremented_str = json_str.replace("1", "2")
    incremented_dict = json.loads(incremented_str)
    update_input = incremented_dict["input"]
    update_data = incremented_dict["data"]

    # Use the same index code as the index we just created, so we update instead of create
    update_input["code"] = created_index.code
    update_data["columns"][0]["code"] = created_index.code

    updated_index, created = _update_or_create_index(update_input, update_data)
    assert created is False
    assert updated_index.code == created_index.code
    assert updated_index.created_at == created_index.created_at
    assert updated_index.modified_at > created_index.modified_at
    assert updated_index.url == "https://test.url.2"
    assert updated_index.name == "Test column text 2"
    assert updated_index.comment == "Test column comment 2"
    assert updated_index.source == "Test data source 2"
    assert updated_index.source_table_updated == datetime(
        year=2024, month=2, day=2, hour=5, tzinfo=timezone.utc
    )
    assert updated_index.source_table_label == "Test source table label 2"


@pytest.mark.django_db
def test_create_or_update_index_number(old_dwellings_price_index_factory):
    """Happy path: new index numbers are saved to DB, and are updated when using
    the same index id and year.
    """
    # Case 1: create new numbers
    creation_input = cast(
        IndexInput,
        {
            "name": "",
            "url": "",
            "code": "test_index_code_1",
        },
    )
    creation_data = cast(
        ResponseData,
        {
            "columns": [
                {
                    "code": "Vuosi",
                    "text": "",
                    "comment": "",
                    "type": "t",
                },
                {"code": "Alue", "text": "", "type": "d"},
                {
                    "code": "test_index_code_1",
                    "text": "",
                    "comment": "",
                    "type": "c",
                },
            ],
            "comments": [],
            "data": [
                {"key": ["2021", "pks"], "values": ["100.1"]},
                {"key": ["2022", "pks"], "values": ["100.2"]},
                {"key": ["2023", "pks"], "values": ["100.3"]},
                {"key": ["2024", "pks"], "values": ["100.4"]},
            ],
            "metadata": [],
        },
    )
    index = old_dwellings_price_index_factory(
        code="test_index_code_1", name="Test index 1", url="https://test.url.1"
    )
    numbers_updated, numbers_created = _update_or_create_index_numbers(
        creation_input, creation_data, index
    )
    assert numbers_updated == 0
    assert numbers_created == 4

    # Case 2: update an existing number
    update_data = deepcopy(creation_data)
    update_data["data"][2]["values"][0] = "200.3"  # change year 2023's index number
    numbers_updated, numbers_created = _update_or_create_index_numbers(
        creation_input, update_data, index
    )
    # Currently all numbers are updated every time, regardless of changes in content.
    # If you want to avoid unnecessary updates, write logic to skip update when nothing changes.
    assert numbers_updated == 4
    assert numbers_created == 0


@pytest.fixture
def real_input_data() -> IndexInput:
    """Inputs for requesting index number details from Tilastokeskus API.

    The only values necessary for the request are the `url` and `code` values.

    The keys are arbitrary, and only for internal reference in our code.
    """
    return {
        "name": "13mq -- Vanhojen osakeasuntojen hintaindeksi (2020=100) ja \
                kauppojen lukumäärät, vuositasolla, 2020-2023",
        "url": "https://pxdata.stat.fi:443/PxWeb/api/v1/en/StatFin/ashi/statfin_ashi_pxt_13mq.px",
        "code": "ketj_P_QA_T",
    }


@pytest.fixture
def columns_real_data() -> list[ColumnItem]:
    """Column items from real API response data."""
    return [
        {"code": "Vuosi", "text": "Year", "type": "t"},
        {"code": "Alue", "text": "Region", "type": "d"},
        {
            "code": "ketj_P_QA_T",
            "text": "Index (2020=100)",
            "comment": "An index is a ratio describing the relative change in a variable (e.g. price, volume or value) compared to a certain base period [e.g. one year]. The index point figure for each point in time tells what percentage the given examined variable is of its respective value or volume at the base point in time. The mean of the index point figures for the base period is 100.\r\n",
            "type": "c",
        },
    ]


@pytest.fixture
def comments_test_data() -> list[CommentItem]:
    """Hypothetical comment items."""
    return [
        {
            "variable": "Vuosi",
            "value": "2022",
            "comment": "* preliminary data\r\n",
        },
        {
            "variable": "Vuosi",
            "value": "2023",
            "comment": "* preliminary data\r\n",
        },
    ]


@pytest.fixture
def datapoints_real_data() -> list[DataPoint]:
    """Data points from real API response data."""
    return [
        {"key": ["2020", "pks"], "values": ["100.0"]},
        {"key": ["2021", "pks"], "values": ["105.6"]},
        {"key": ["2022", "pks"], "values": ["105.7"]},
        {"key": ["2023", "pks"], "values": ["97.4"]},
    ]


@pytest.fixture
def metadata_real_data() -> list[MetadataItem]:
    """Metadata items from real API response data."""
    return [
        {
            "updated": "2024-05-03T05.00.00Z",
            "label": "Price index of old dwellings in housing companies (2020=100) and numbers of transactions, yearly by Year, Region and Information",
            "source": "Statistics Finland, prices of dwellings in housing companies",
        }
    ]


@pytest.fixture
def real_data(
    columns_real_data,
    datapoints_real_data,
    metadata_real_data,
) -> ResponseData:
    """The combined real API response data in the expected format."""
    return {
        "columns": columns_real_data,
        "comments": [],
        "data": datapoints_real_data,
        "metadata": metadata_real_data,
    }
