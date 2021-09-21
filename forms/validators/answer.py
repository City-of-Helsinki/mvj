import re

from rest_framework.serializers import ValidationError


class SocialSecurityValidator:
    def __call__(self, value):
        for entry in value["entries"]:
            if entry["field"].identifier == "henkilotunnus":
                if not re.search("^[0-9]{6}[+Aa-][0-9]{3}[A-z0-9]$", entry["value"]):
                    raise ValidationError(code="invalid_ssn")


class RequiredFormFieldValidator:
    def __call__(self, value):
        for section in value["form"].sections.all():
            for field in section.field_set.all():
                if not field.required:
                    continue
                found = False
                for entry in value["entries"]:
                    if entry["field"].id == field.id and entry["value"] != "":
                        found = True
                        continue
                if not found:
                    raise ValidationError(code="required")
