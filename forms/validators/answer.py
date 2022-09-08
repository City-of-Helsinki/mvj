import re
from typing import Iterable

from rest_framework.serializers import ValidationError

from forms.models import Field


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
    EMPTY_VALUES = ["", [], None]

    def __call__(self, value):
        self.required_validator(
            value["entries"],
            Field.objects.filter(section__form=value["form"], required=True),
        )

    def required_validator(
        self, entries, required_fields, section_identifier=None, field_identifier=None
    ):
        if not isinstance(entries, Iterable) or isinstance(entries, str):
            return
        if "sections" in entries:
            self.required_validator(entries["sections"], required_fields, None)
        if "fields" in entries:
            self.required_validator(
                entries["fields"], required_fields, section_identifier
            )
        if isinstance(entries, list):
            for i, entry in enumerate(entries):
                self.required_validator(
                    entry, required_fields, section_identifier=section_identifier
                )
            return
        if section_identifier is not None:
            for entry in entries:
                if (
                    required_fields.filter(
                        section__identifier=section_identifier, identifier=entry
                    ).exists()
                    and entries[entry]["value"] in self.EMPTY_VALUES
                ):
                    raise ValidationError(code="required")
        for entry in entries:
            section_identifier = re.sub(r"\[\d+]", "", entry)
            self.required_validator(
                entries[entry], required_fields, section_identifier=section_identifier
            )
