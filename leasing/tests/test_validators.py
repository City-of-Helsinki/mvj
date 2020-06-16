import pytest
from django.core.exceptions import ValidationError

from leasing import validators


def test_business_id_validator():
    validators.validate_business_id("1234567-8")

    with pytest.raises(ValidationError):
        validators.validate_business_id("1234567-")

    with pytest.raises(ValidationError):
        validators.validate_business_id("1234567-89")
