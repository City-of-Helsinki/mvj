from leasing.report.invoice.invoicing_review import InvoicingReviewReport


def test_get_worksheet_names_dict():
    test_data_sections = {
        "test_name": 1,
        "test_name_test_name_test_name_test_name_1": 2,
        "test_name_test_name_test_name_test_name_2": 3,
        "test_name_test_name_test_name_test_name_3": 4,
        "long_name_long_name_long_name_long_name": 5,
    }

    expected_result_contain_values = [
        "test_name",
        "test_name_test_name_test_name..",
        "test_name_test_name_test_name_2",
        "test_name_test_name_test_name_3",
        "long_name_long_name_long_name..",
    ]

    result_dict = InvoicingReviewReport.get_worksheet_names_dict(
        None, test_data_sections
    )

    result_values = list(map(lambda kv: kv[1], result_dict.items()))

    for expected_value in expected_result_contain_values:
        assert expected_value in result_values
