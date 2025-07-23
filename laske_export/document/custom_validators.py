from django.core.exceptions import ValidationError


def calculate_checksum(value: str | None) -> int | None:
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

    return (10 - (total % 10)) % 10
