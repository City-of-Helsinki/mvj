from copy import deepcopy

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
    _extract_numbers_from_quarter_name,
    _find_comment_for_value,
    _find_key_position,
    _find_value_position,
    _get_update_date,
    _update_or_create_index,
    _update_or_create_index_numbers,
)
from leasing.models.rent import IndexNumber, OldDwellingsInHousingCompaniesPriceIndex

# from django.core.management import call_command


# TODO don't test a low-level function if testing a top-level function includes
# that function in happy/neutral/unhappy path


def test_quarterly_response_data_is_valid(
    quarterly_real_input_data: IndexInput,
    quarterly_real_test_data: ResponseData,
):
    """Happy path with valid data: no exception is raised."""
    try:
        _check_that_response_data_is_valid(
            quarterly_real_input_data, quarterly_real_test_data
        )
    except ResponseDataError as e:
        pytest.fail(f"An error was raised for valid data: {e}")


def test_missing_column_raises(
    quarterly_real_input_data: IndexInput, quarterly_real_test_data: ResponseData
):
    """Unhappy path with missing columns in the response.

    Unclear whether this kind of response is possible, but if such happens it
    should raise an error.
    """
    quarterly_real_test_data["columns"] = {}
    with pytest.raises(ResponseDataError):
        _check_that_response_data_is_valid(
            quarterly_real_input_data, quarterly_real_test_data
        )


def test_key_position_found(columns_quarterly_real_test_data: list[ColumnItem]):
    """Happy path: key positions are correctly identified in the data."""
    assert _find_key_position(columns_quarterly_real_test_data, "Vuosineljännes") == 0
    assert _find_key_position(columns_quarterly_real_test_data, "Alue") == 1


def test_key_column_missing_code_raises(
    columns_quarterly_real_test_data: list[ColumnItem],
):
    """Unhappy path: the key column cannot be found in the data because code doesn't match."""
    code_not_present = deepcopy(columns_quarterly_real_test_data)
    for column in code_not_present:
        column["code"] = "Something else"

    with pytest.raises(ResponseDataError):
        _find_key_position(code_not_present, "Vuosineljännes")


def test_key_column_wrong_type_raises(
    columns_quarterly_real_test_data: list[ColumnItem],
):
    """Unhappy path: the key column cannot be found in the data because type doesn't match."""
    type_is_wrong = deepcopy(columns_quarterly_real_test_data)
    for column in type_is_wrong:
        # type c indicates a measure column instead of a key column
        column["type"] = "c"

    with pytest.raises(ResponseDataError):
        _find_key_position(type_is_wrong, "Vuosineljännes")


def test_value_position_found(
    quarterly_real_input_data: IndexInput,
    columns_quarterly_real_test_data: list[ColumnItem],
):
    """Happy path: value positions are correctly identified in the data."""
    index_code = quarterly_real_input_data["code"]
    assert _find_value_position(columns_quarterly_real_test_data, index_code) == 0


def test_comment_matched(
    datapoints_quarterly_real_test_data: list[DataPoint],
    comments_quarterly_real_test_data: list[CommentItem],
    columns_quarterly_real_test_data: list[ColumnItem],
):
    """Happy path: a comment is properly matched to a data point."""
    dp_with_comment = datapoints_quarterly_real_test_data[-1]
    assert (
        _find_comment_for_value(
            dp_with_comment,
            comments_quarterly_real_test_data,
            columns_quarterly_real_test_data,
        )
        == "* ennakkotieto\r\n"
    )


def test_comment_not_matched(
    datapoints_quarterly_real_test_data: list[DataPoint],
    comments_quarterly_real_test_data: list[CommentItem],
    columns_quarterly_real_test_data: list[ColumnItem],
):
    """Happy path: a comment is not matched to non-matching data point."""
    dp_without_comment = datapoints_quarterly_real_test_data[0]
    assert (
        _find_comment_for_value(
            dp_without_comment,
            comments_quarterly_real_test_data,
            columns_quarterly_real_test_data,
        )
        == ""
    )


@pytest.mark.skip(reason="test not implemented yet")
def test_get_update_date_valid():
    # TODO happy path
    pass


@pytest.mark.skip(reason="test not implemented yet")
def test_get_update_date_invalid():
    # TODO unhappy path
    pass


@pytest.mark.skip(reason="test not implemented yet")
def test_extract_numbers_from_quarter_name_valid():
    # TODO happy path
    pass


@pytest.mark.skip(reason="test not implemented yet")
def test_extract_numbers_from_quarter_name_invalid():
    # TODO unhappy path
    pass


@pytest.mark.skip(reason="test not implemented yet")
def test_cast_index_number_to_float():
    # TODO happy path to float
    pass


@pytest.mark.skip(reason="test not implemented yet")
def test_cast_index_number_to_none():
    # TODO happy path to None
    pass


@pytest.mark.skip(reason="test not implemented yet")
def test_cast_index_number_invalid():
    # TODO unhappy path
    # TODO implement try-catch and error logging to source
    pass


@pytest.mark.skip(reason="test not implemented yet")
def test_create_index():
    # TODO happy path
    pass


@pytest.mark.skip(reason="test not implemented yet")
def test_update_index():
    # TODO happy path
    pass


@pytest.mark.skip(reason="test not implemented yet")
def test_create_index_number():
    # TODO happy path
    pass


@pytest.mark.skip(reason="test not implemented yet")
def test_update_index_number():
    # TODO happy path
    pass


@pytest.fixture
def quarterly_real_input_data() -> IndexInput:
    """Inputs for requesting index number details from Tilastokeskus API.

    The only values necessary for the request are the `url` and `code` values.

    The keys are arbitrary, and only for internal reference in our code.
    """
    return {
        "name": "13mp -- Price index of old dwellings in housing companies (2020=100) \
                and numbers of transactions, quarterly",
        "url": "https://pxdata.stat.fi:443/PxWeb/api/v1/en/StatFin/ashi/statfin_ashi_pxt_13mp.px",
        "code": "ketj_P_QA_T",
    }


@pytest.fixture
def columns_quarterly_real_test_data() -> list[ColumnItem]:
    """Column items from real API response data."""
    return [
        {
            "code": "Vuosineljännes",
            "text": "Vuosineljännes",
            "comment": "* ennakkotieto\r\n",
            "type": "t",
        },
        {"code": "Alue", "text": "Alue", "type": "d"},
        {
            "code": "ketj_P_QA_T",
            "text": "Indeksi (2020=100)",
            "comment": "Indeksi on suhdeluku, joka kuvaa jonkin muuttujan \
            (esimerkiksi hinnan, määrän tai arvon) suhteellista muutosta \
            perusjakson (esimerkiksi vuoden) suhteen. Kunkin ajankohdan \
            indeksipisteluku ilmoittaa, kuinka monta prosenttia kyseisen \
            ajankohdan tarkasteltava muuttuja on perusjakson arvosta tai \
            määrästä. Perusjakson indeksipistelukujen keskiarvo on 100. \
            Tilastossa julkaistavat hintaindeksit ovat laatuvakioituja ja niiden \
            kehitys voi poiketa neliöhintojen kehityksestä.\r\n",
            "type": "c",
        },
    ]


@pytest.fixture
def comments_quarterly_real_test_data() -> list[CommentItem]:
    """Comment items from real API response data."""
    return [
        {
            "variable": "Vuosineljännes",
            "value": "2024Q1",
            "comment": "* ennakkotieto\r\n",
        },
        {
            "variable": "Vuosineljännes",
            "value": "2024Q2",
            "comment": "* ennakkotieto\r\n",
        },
    ]


@pytest.fixture
def datapoints_quarterly_real_test_data() -> list[DataPoint]:
    """Data points from real API response data."""
    return [
        {"key": ["2020Q1", "pks"], "values": ["98.5"]},
        {"key": ["2020Q2", "pks"], "values": ["100.1"]},
        {"key": ["2020Q3", "pks"], "values": ["100.1"]},
        {"key": ["2020Q4", "pks"], "values": ["101.3"]},
        {"key": ["2021Q1", "pks"], "values": ["103.8"]},
        {"key": ["2021Q2", "pks"], "values": ["106.1"]},
        {"key": ["2021Q3", "pks"], "values": ["105.8"]},
        {"key": ["2021Q4", "pks"], "values": ["106.9"]},
        {"key": ["2022Q1", "pks"], "values": ["106.7"]},
        {"key": ["2022Q2", "pks"], "values": ["108.0"]},
        {"key": ["2022Q3", "pks"], "values": ["105.6"]},
        {"key": ["2022Q4", "pks"], "values": ["102.5"]},
        {"key": ["2023Q1", "pks"], "values": ["99.7"]},
        {"key": ["2023Q2", "pks"], "values": ["98.7"]},
        {"key": ["2023Q3", "pks"], "values": ["96.6"]},
        {"key": ["2023Q4", "pks"], "values": ["94.8"]},
        {"key": ["2024Q1", "pks"], "values": ["93.6"]},
        {"key": ["2024Q2", "pks"], "values": ["93.7"]},
    ]


@pytest.fixture
def metadata_quarterly_real_test_data() -> list[MetadataItem]:
    """Metadata items from real API response data."""
    return [
        {
            "updated": "2024-07-26T05.00.00Z",
            "label": "Vanhojen osakeasuntojen hintaindeksi (2020=100) ja \
            kauppojen lukumäärät, neljännesvuosittain muuttujina Vuosineljännes, \
            Alue ja Tiedot",
            "source": "Tilastokeskus, osakeasuntojen hinnat",
        }
    ]


@pytest.fixture
def quarterly_real_test_data(
    columns_quarterly_real_test_data,
    comments_quarterly_real_test_data,
    datapoints_quarterly_real_test_data,
    metadata_quarterly_real_test_data,
) -> ResponseData:
    """The combined real API response data in the expected format."""
    return {
        "columns": columns_quarterly_real_test_data,
        "comments": comments_quarterly_real_test_data,
        "data": datapoints_quarterly_real_test_data,
        "metadata": metadata_quarterly_real_test_data,
    }
