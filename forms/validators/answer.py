import re
from typing import Iterable

from rest_framework.serializers import ValidationError

from forms.models import Field

SSN_CHECK = [
    "0",
    "1",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9",
    "A",
    "B",
    "C",
    "D",
    "E",
    "F",
    "H",
    "J",
    "K",
    "L",
    "M",
    "N",
    "P",
    "R",
    "S",
    "T",
    "U",
    "V",
    "W",
    "X",
    "Y",
]


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
                if isinstance(entries[entry], str) or entry in ("value", "extraValue"):
                    continue

                self.regex_checker(entries, entry, regex_fields, section_identifier)
        for entry in entries:
            section_identifier = re.sub(r"\[\d+]", "", entry)
            self.regex_validator(
                entries[entry], regex_fields, section_identifier=section_identifier
            )

    def regex_checker(self, entries, entry, regex_fields, section_identifier):
        if regex_fields.filter(
            section__identifier=section_identifier, identifier=entry
        ).exists():
            if entries[entry]["value"] == "":
                return

            regex_exists = bool(re.search(self._regex, entries[entry]["value"]))
            if regex_exists and self._identifier == "henkilotunnus":
                self.ssn_checker(entries[entry]["value"])
            if not regex_exists:
                raise ValidationError(code=self._error_code)

    def ssn_checker(self, ssn_parts):
        ssn_number = int(ssn_parts[0:6] + ssn_parts[7:-1])
        if SSN_CHECK[ssn_number % 31] != ssn_parts[-1]:
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


class ControlShareValidation:
    def __call__(self, value):
        result = 0
        for control_share in self.control_share_finder_generator(value["entries"]):
            values = control_share.split("/")
            result += int(values[0]) / int(values[1])
        if round(result, 10) != 1:
            raise ValidationError(code="control share is not even")

    def control_share_finder_generator(self, entries):
        if not isinstance(entries, Iterable) or isinstance(entries, str):
            return
        if "hallintaosuus" in entries:
            yield entries["hallintaosuus"]["value"]
        if isinstance(entries, list):
            for entry in entries:
                yield from self.control_share_finder_generator(entry)
            return
        for entry in entries:
            yield from self.control_share_finder_generator(entries[entry])
