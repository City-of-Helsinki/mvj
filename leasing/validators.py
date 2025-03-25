from django.core import validators as core_validators
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _

business_id_re = core_validators._lazy_re_compile(r"^.{9}$")
validate_business_id = core_validators.RegexValidator(
    business_id_re, _("Enter a valid business id."), "invalid"
)


class HexColorValidator(RegexValidator):
    # Startswith `#`, then has either 1 or 2 groups of 3 characters
    # that are 0-9 or a-f or A-F
    regex = r"^#(?:[0-9a-fA-F]{3}){1,2}$"
    message = "Enter a valid hex color code, e.g. #000000 or #FFF"
