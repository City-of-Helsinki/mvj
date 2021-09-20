from rest_framework.serializers import ValidationError


class SocialSecurityValidator:
    pass


class RequiredFormFieldValidator:
    def __call__(self, value):
        for section in value['form'].sections.all():
            for field in section.field_set.all():
                if not field.required:
                    continue
                found = False
                for entry in value["entries"]:
                    if entry['field'].id == field.id and entry['value'] != "":
                        found = True
                        continue
                if not found:
                    raise ValidationError(code='required')
