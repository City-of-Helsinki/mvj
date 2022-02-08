import re

from rest_framework.serializers import ValidationError


class FieldRegexValidator:
    """
    Do Regex validation for form answer entries
    """

    def __init__(self, regex, error_code, identifier):
        self._regex = regex
        self._error_code = error_code
        self._identifier = identifier

    def __call__(self, value):
        for entry in value["entries"]:
            if entry == self._identifier:
                if not re.search(
                    self._regex, list(value["entries"][entry][self._identifier])[0]
                ):
                    raise ValidationError(code=self._error_code)
            for sub_entry in value["entries"][entry]:
                if sub_entry == self._identifier:
                    if not re.search(self._regex, value["entries"][entry][sub_entry]):
                        raise ValidationError(code=self._error_code)


class RequiredFormFieldValidator:
    def __call__(self, value):
        for section in value["form"].sections.all():
            for field in section.fields.all():
                if not field.required:
                    continue
                found = False
                if (
                    field.identifier
                    in list(value["entries"][section.identifier].keys())
                    and value["entries"][section.identifier][field.identifier] != ""
                ):
                    found = True
                    continue
                if not found:
                    raise ValidationError(code="required")
