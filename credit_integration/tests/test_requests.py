from credit_integration.requests import _build_query_parameters


def test_build_query_parameters_duplicate_keys_as_list():
    query_params = {"version": "5.01", "someList": ["ABC", "123"]}
    assert _build_query_parameters(query_params) == (
        "version=5.01&someList=ABC&someList=123"
    )


def test_query_parameters_none_not_included():
    query_params = {"version": "5.01", "someList": ["ABC", "123"], "noneValue": None}
    assert _build_query_parameters(query_params) == (
        "version=5.01&someList=ABC&someList=123"
    )
