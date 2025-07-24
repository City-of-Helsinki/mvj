from django.core.exceptions import ValidationError


def calculate_checksum(value: str | None) -> str | None:
    """
    Calculates the checksum for digits of the payment reference (excluding the last digit)
    """
    if not value:
        return None

    if not value.isdigit():
        raise ValidationError("Payment reference must be numeric.")

    coefficients = [7, 3, 1]
    reversed_value = value[::-1]
    digits_paired_with_coefficients = [
        (int(digit), coefficients[i % len(coefficients)])
        for i, digit in enumerate(reversed_value)
    ]

    total = sum(
        int(digit) * coefficient
        for digit, coefficient in digits_paired_with_coefficients
    )

    return str((10 - (total % 10)) % 10)


def validate_payment_reference(value):
    if value and not value.isdigit():
        raise ValidationError("Payment reference must contain only digits.")

    if value:
        reference, checksum = value[:-1], value[-1]

        expected_checksum = calculate_checksum(reference)

        if expected_checksum != checksum:
            raise ValidationError("Invalid payment reference: checksum does not match.")
