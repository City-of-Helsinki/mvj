import pytest
from constance.test import override_config
from django.forms import ValidationError

from laske_export.document.custom_validators import (
    calculate_checksum,
    validate_payment_reference,
)


@pytest.mark.django_db
@override_config(LASKE_EXPORT_ANNOUNCE_EMAIL=None)
def test_calculate_checksum():
    result = calculate_checksum("1234")
    assert result == "4"  # Total sum is 46, last digit is 4

    result = calculate_checksum("123456789")
    assert result == "7"  # Total sum is 183, last digit is 7


@pytest.mark.django_db
@override_config(LASKE_EXPORT_ANNOUNCE_EMAIL=None)
def test_calculate_checksum_nondigit_input():
    with pytest.raises(ValidationError):
        calculate_checksum(None)
    with pytest.raises(ValidationError):
        calculate_checksum("")
    with pytest.raises(ValidationError):
        calculate_checksum("123a")
    with pytest.raises(ValidationError):
        calculate_checksum("12.34")
    with pytest.raises(ValidationError):
        calculate_checksum("12 34")


@pytest.mark.django_db
@override_config(LASKE_EXPORT_ANNOUNCE_EMAIL=None)
def test_validate_payment_reference():
    # Valid values
    validate_payment_reference("12344")
    validate_payment_reference("1234567897")  # Last digit is checksum

    # Invalid values
    with pytest.raises(ValidationError):
        validate_payment_reference(None)
    with pytest.raises(ValidationError):
        validate_payment_reference("")
    with pytest.raises(ValidationError):
        validate_payment_reference("12abc340")
    with pytest.raises(ValidationError):
        validate_payment_reference("12340")
    with pytest.raises(ValidationError):
        validate_payment_reference("1234567890")
