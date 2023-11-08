import inspect
from collections import OrderedDict
from collections.abc import Iterable

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from lxml import etree


def recursive_members(obj):
    object_members = list(obj.__dict__)
    if obj.__bases__:
        for base in obj.__bases__:
            object_members.extend(recursive_members(base))

    return object_members


class FieldError(Exception):
    pass


class Field:
    def __init__(
        self,
        name=None,
        field_type="string",
        validators=None,
        many=False,
        required=False,
    ):
        self.element_name = name
        self.field_type = field_type
        self.validators = validators
        self.many = many
        self.required = required
        self.validation_errors = []

    def _validate_value(self, value):
        for one_value in value:
            if self.field_type == "string" and not isinstance(one_value, str):
                self.validation_errors.append(_("Value should be a string"))
            elif inspect.isclass(self.field_type) and not isinstance(
                one_value, self.field_type
            ):
                self.validation_errors.append(
                    _("Value should be of type {}".format(self.field_type))
                )

            if not self.validators:
                continue

            for validator in self.validators:
                try:
                    validator(one_value)
                except ValidationError as err:
                    self.validation_errors.append(err.messages)

    def is_valid(self, value):
        self.validation_errors = []

        if self.required and not value:
            self.validation_errors.append(_("Value is required"))

        if not value:
            return True

        if self.many:
            if isinstance(value, str) or not isinstance(value, Iterable):
                self.validation_errors.append(_("Value should be an Iterable"))
                return False
        else:
            value = [value]

        self._validate_value(value)

        if len(self.validation_errors):
            return False

        return True


class FieldGroup:
    def __init__(self):
        self._fields = self.get_fields()
        self.validation_errors = []

    def _validate_fields(self):
        self.validation_errors = []
        error_list = {}

        for field_name, field in self.get_fields().items():
            field_value = getattr(self, field_name)

            if not field.is_valid(field_value):
                error_list[field_name] = field.validation_errors

            if not field_value:
                continue

            if not field.many:
                field_value = [field_value]

            for one_value in field_value:
                if field.field_type == "string":
                    continue
                elif issubclass(field.field_type, FieldGroup):
                    one_value.validate()

        if len(error_list) > 0:
            raise ValidationError(error_list)

    def get_fields(self):
        if hasattr(self, "_fields"):
            return self._fields

        fields = OrderedDict()

        members = inspect.getmembers(self, lambda o: isinstance(o, Field))
        # inspect.getmembers returns members in alphabetical order, reorder them
        # in the declaration order. (__dict__ is in order in Python 3.6+)
        class_members_order = recursive_members(self.__class__)

        members.sort(key=lambda o: class_members_order.index(o[0]))

        for i in members:
            fields[i[0]] = i[1]
            setattr(self, i[0], None)

        return fields

    def get_fields_as_elements(self):
        elements = []

        for field_name, field in self.get_fields().items():
            field_value = getattr(self, field_name)

            if not field.is_valid(field_value):
                raise FieldError(
                    "Value ({}) of field {} is not valid".format(
                        field_value, field_name
                    )
                )

            if not field_value:
                el = etree.Element(field.element_name)
                elements.append(el)
                continue

            if not field.many:
                field_value = [field_value]

            for one_value in field_value:
                if field.field_type == "string":
                    el = etree.Element(field.element_name)
                    el.text = one_value
                    elements.append(el)
                elif issubclass(field.field_type, FieldGroup):
                    elements.append(one_value.to_etree())
                else:
                    # TODO: error
                    pass

        return elements

    def to_etree(self):
        elements = self.get_fields_as_elements()
        root = etree.Element(self.Meta.element_name)
        for el in elements:
            root.append(el)

        return root

    def to_xml_string(self, encoding="utf-8"):
        root = self.to_etree()

        return etree.tostring(
            root, encoding=encoding, xml_declaration=True, pretty_print=True
        )

    def validate(self):
        self._validate_fields()

    def __str__(self):
        return self.to_xml_string()
