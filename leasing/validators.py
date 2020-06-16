from django.core import validators as core_validators
from django.utils.translation import gettext_lazy as _

business_id_re = core_validators._lazy_re_compile(r"^.{9}$")
validate_business_id = core_validators.RegexValidator(
    business_id_re, _("Enter a valid business id."), "invalid"
)
