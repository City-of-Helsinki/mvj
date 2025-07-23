import pytest
from constance.test import override_config

from laske_export.document.custom_validators import calculate_checksum


@pytest.mark.django_db
@override_config(LASKE_EXPORT_ANNOUNCE_EMAIL=None)
def test_calculate_checksum():
    result = calculate_checksum("1234")
    assert result == 4  # Total sum is 46, last digit is 4

    result = calculate_checksum("123456789")
    assert result == 7  # Total sum is 183, last digit is 7


@pytest.mark.django_db
@override_config(LASKE_EXPORT_ANNOUNCE_EMAIL=None)
def test_calculate_checksum_nondigit_input():
    result = calculate_checksum(None)
    assert result is None
    result = calculate_checksum("")
    assert result is None
    with pytest.raises(ValidationError):
        calculate_checksum("123a")
    with pytest.raises(ValidationError):
        calculate_checksum("12.34")
    with pytest.raises(ValidationError):
        calculate_checksum("12 34")
