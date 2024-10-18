import pytest
from rest_framework.exceptions import ValidationError

from leasing.serializers.utils import validate_seasonal_day_for_month


def test_validate_seasonal_day_for_month():
    # Test valid cases
    try:
        validate_seasonal_day_for_month(1, 1)
        validate_seasonal_day_for_month(28, 2)
        validate_seasonal_day_for_month(30, 4)
        validate_seasonal_day_for_month(31, 12)
        validate_seasonal_day_for_month(None, None)  # No values to validate
    except ValidationError:
        pytest.fail("validate_seasonal_day_for_month() raised ValidationError!")

    # Test month not within bounds
    day, month = 1, 0
    with pytest.raises(ValidationError) as exc:
        validate_seasonal_day_for_month(day, month)
    assert (
        exc.value.detail.get("month")
        == f"Invalid month: {month}. Month must be between 1 and 12."
    )
    day, month = 1, 13
    with pytest.raises(ValidationError) as exc:
        validate_seasonal_day_for_month(day, month)
    assert (
        exc.value.detail.get("month")
        == f"Invalid month: {month}. Month must be between 1 and 12."
    )

    # Test day not within bounds
    day, month = 0, 1
    with pytest.raises(ValidationError) as exc:
        validate_seasonal_day_for_month(day, month)
    assert exc.value.detail.get("day") == f"Invalid day: {day} for month: {month}"

    # Does not take leap years into account, as it is not a calendar day (with year)
    day, month = 29, 2
    with pytest.raises(ValidationError) as exc:
        validate_seasonal_day_for_month(day, month)
    assert exc.value.detail.get("day") == f"Invalid day: {day} for month: {month}"

    # Test day and month provided
    day, month = 1, None
    with pytest.raises(ValidationError) as exc:
        validate_seasonal_day_for_month(day, month)
    assert exc.value.detail.get("month") == "Both day and month must be provided"

    day, month = None, 1
    with pytest.raises(ValidationError) as exc:
        validate_seasonal_day_for_month(day, month)
    assert exc.value.detail.get("day") == "Both day and month must be provided"

    # Test invalid types
    day, month = "2", 1
    with pytest.raises(ValidationError) as exc:
        validate_seasonal_day_for_month(day, month)
    assert exc.value.detail.get("day") == "Day must be an integer"

    day, month = 2, "1"
    with pytest.raises(ValidationError) as exc:
        validate_seasonal_day_for_month(day, month)
    assert exc.value.detail.get("month") == "Month must be an integer"
