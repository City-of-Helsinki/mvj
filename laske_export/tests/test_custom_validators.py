import pytest
from django.core.exceptions import ValidationError
from django.test import override_settings

from laske_export.document.custom_validators import validate_payment_reference


@pytest.mark.django_db
@override_settings(LASKE_EXPORT_ANNOUNCE_EMAIL=None)
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
