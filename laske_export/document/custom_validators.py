from django.core.exceptions import ValidationError

from laske_export.utils import calculate_payment_reference_checksum


def validate_payment_reference(value: str | None) -> None:
    if not value or value == "":
        raise ValidationError("Payment reference cannot be None or empty.")

    if value and not value.isdigit():
        raise ValidationError("Payment reference must contain only digits.")

    if value:
        reference, checksum = value[:-1], value[-1]

        expected_checksum = calculate_payment_reference_checksum(reference)

        if expected_checksum != checksum:
            raise ValidationError("Invalid payment reference: checksum does not match.")
