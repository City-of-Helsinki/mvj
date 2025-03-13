import pytest
from django.core.exceptions import ValidationError

from leasing import validators
from leasing.models.map_layers import HexColorValidator


def test_business_id_validator():
    validators.validate_business_id("1234567-8")

    with pytest.raises(ValidationError):
        validators.validate_business_id("1234567-")

    with pytest.raises(ValidationError):
        validators.validate_business_id("1234567-89")


@pytest.fixture
def validator():
    return HexColorValidator()


@pytest.mark.parametrize(
    "hex_color",
    [
        "#FFFFFF",
        "#000000",
        "#FFF",
        "#000",
        "#1F2A3B",
    ],
)
def test_valid_hex_color(validator, hex_color):
    try:
        validator(hex_color)
    except ValidationError:
        pytest.fail("ValidationError was raised")


@pytest.mark.parametrize(
    "hex_color",
    [
        "FFFFFF",
        "123",
        "#00",
        "#FF00",
        "#GGG",
        "#1A2B3Z",
    ],
)
def test_invalid_hex_color(validator, hex_color):
    with pytest.raises(ValidationError):
        validator(hex_color)
