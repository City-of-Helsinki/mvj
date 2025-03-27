import re

import pytest

from sanitizers.mvj import (
    sanitize_national_identification_number,
    sanitize_national_identification_number_if_exist,
)

# Regular expression for approximately validating the format of a Finnish national identification number
HETU_REGEX = r"^\d{6}A\d{3}[0-9A-Y]$"


def test_national_identification_number_format():
    """Test that the generated national identification number ("hetu") follows the correct format."""
    for _ in range(100):  # Test multiple times to increase confidence
        hetu = sanitize_national_identification_number(None)

        # Check basic format: DDMMYYA###C
        assert re.match(HETU_REGEX, hetu)

        # Extract components for further validation
        day = int(hetu[0:2])
        month = int(hetu[2:4])
        year = int(hetu[4:6])
        century_marker = hetu[6]
        individual_number = int(hetu[7:10])
        control_char = hetu[10]

        # Validate ranges
        assert 1 <= day <= 31
        assert 1 <= month <= 12
        assert (
            50 <= year <= 99
        )  # Should be between 2050-2099, to avoid collisions with existing numbers
        assert century_marker == "A"  # For years 2000-2099
        assert 1 <= individual_number <= 899

        # Validate control character calculation
        number_for_calculation = int(
            f"{day:02d}{month:02d}{year:02d}{individual_number:03d}"
        )
        control_number = number_for_calculation % 31
        control_chars = "0123456789ABCDEFHJKLMNPRSTUVWXY"
        expected_control_char = control_chars[control_number]
        assert control_char == expected_control_char


def test_national_identification_number_uniqueness():
    """Test that multiple calls produce different identification numbers."""
    unique_results = set()
    for _ in range(100):
        hetu = sanitize_national_identification_number(None)
        unique_results.add(hetu)

    assert len(unique_results) > 95  # allow for rare collisions


def test_national_identification_number_if_exist():
    """Test the if_exist variant of the function."""
    # Should return None when None is passed
    assert sanitize_national_identification_number_if_exist(None) is None

    # Should return a valid national ID when a value is passed
    result = sanitize_national_identification_number_if_exist("anything")
    if not result:
        pytest.fail("Expected a value, got None")

    assert re.match(HETU_REGEX, result)
