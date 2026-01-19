import pytest
from django.core.exceptions import ValidationError

from laske_export.document.sales_order import LineItem, normalize_short_lines


# Skip fixture marked `autouse=True`
@pytest.fixture
def laske_export_from_email():
    return


# Skip fixture marked `autouse=True`
@pytest.fixture
def laske_export_announce_email():
    return


def test_line_item_tax_code_validation():
    """Tests one MaxLengthValidator works."""
    line_item = LineItem()
    # No ValidationError is expected
    line_item.validate()

    # Test that MaxLengthValidators work
    line_item.tax_code = "12"  # Expected max length is 1
    with pytest.raises(ValidationError) as exc:
        line_item.validate()
    assert "tax_code" in exc.value.error_dict

    line_item.tax_code = "1"
    # No ValidationError is expected
    line_item.validate()


def test_line_item_only_one_of_set_validation():
    """Tests that setting both 'order_item_number' and 'wbs_element' is not allowed."""
    line_item = LineItem()

    # Test that only one of 'order_item_number' or 'wbs_element' can be set.
    line_item.order_item_number = "1"
    line_item.wbs_element = "1"
    with pytest.raises(ValidationError) as exc:
        line_item.validate()
    assert (
        exc.value.message
        == "Only one of 'order_item_number' or 'wbs_element' can be set."
    )

    line_item = LineItem()
    line_item.order_item_number = "1"
    line_item.validate()

    line_item = LineItem()
    line_item.wbs_element = "1"
    line_item.validate()


def test_normalize_short_lines_single_char():
    """Tests that a single non-whitespace character gets a dot appended."""
    assert normalize_short_lines("1") == "1."
    assert normalize_short_lines("a") == "a."
    assert normalize_short_lines(" 1") == " 1."
    assert normalize_short_lines("1 ") == "1 ."
    assert normalize_short_lines("  a  ") == "  a  ."


def test_normalize_short_lines_multiple_chars():
    """Tests that strings with more than one non-whitespace character remain unchanged."""
    assert normalize_short_lines("ab") == "ab"
    assert normalize_short_lines("123") == "123"
    assert normalize_short_lines("hello") == "hello"
    assert normalize_short_lines("  ab  ") == "  ab  "


def test_normalize_short_lines_empty_or_whitespace():
    """Tests that empty strings or whitespace-only strings remain unchanged."""
    assert normalize_short_lines("") == ""
    assert normalize_short_lines(" ") == ""
    assert normalize_short_lines("   ") == ""
