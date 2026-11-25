import pytest
from django.core.exceptions import ValidationError
from django.test import override_settings

from laske_export.utils import calculate_payment_reference_checksum


@pytest.mark.django_db
@override_settings()
def test_calculate_checksum():
    result = calculate_payment_reference_checksum("1234")
    assert result == "4"  # Total sum is 46, last digit is 4

    result = calculate_payment_reference_checksum("123456789")
    assert result == "7"  # Total sum is 183, last digit is 7


@pytest.mark.django_db
@override_settings()
def test_calculate_checksum_nondigit_input():
    with pytest.raises(ValidationError):
        calculate_payment_reference_checksum(None)
    with pytest.raises(ValidationError):
        calculate_payment_reference_checksum("")
    with pytest.raises(ValidationError):
        calculate_payment_reference_checksum("123a")
    with pytest.raises(ValidationError):
        calculate_payment_reference_checksum("12.34")
    with pytest.raises(ValidationError):
        calculate_payment_reference_checksum("12 34")
