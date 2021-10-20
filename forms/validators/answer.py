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
            if entry["field"].identifier == self._identifier:
                if not re.search(self._regex, entry["value"]):
                    raise ValidationError(code=self._error_code)


class RequiredFormFieldValidator:
    def __call__(self, value):
        for section in value["form"].sections.all():
            for field in section.fields.all():
                if not field.required:
                    continue
                found = False
                for entry in value["entries"]:
                    if entry["field"].id == field.id and entry["value"] != "":
                        found = True
                        continue
                if not found:
                    raise ValidationError(code="required")
