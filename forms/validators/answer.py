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
        self.regex_validator(
            value["entries"],
            Field.objects.filter(
                section__form=value["form"], identifier=self._identifier
            ),
        )

    def regex_validator(
        self, entries, regex_fields, section_identifier=None, field_identifier=None
    ):
        if not isinstance(entries, Iterable) or isinstance(entries, str):
            return
        if "sections" in entries:
            self.regex_validator(entries["sections"], regex_fields, None)
        if "fields" in entries:
            self.regex_validator(entries["fields"], regex_fields, section_identifier)

        if isinstance(entries, list):
            for i, entry in enumerate(entries):
                self.regex_validator(
                    entry, regex_fields, section_identifier=section_identifier
                )
            return

        if section_identifier is not None:
            for entry in entries:
                if regex_fields.filter(
                    section__identifier=section_identifier, identifier=entry
                ).exists() and not re.search(self._regex, entries[entry]["value"]):
                    raise ValidationError(code=self._error_code)
        for entry in entries:
            section_identifier = re.sub(r"\[\d+]", "", entry)
            self.regex_validator(
                entries[entry], regex_fields, section_identifier=section_identifier
            )


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
