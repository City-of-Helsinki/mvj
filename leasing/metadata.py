from django.utils.encoding import force_text
from enumfields.drf import EnumField
from rest_framework.fields import DecimalField
from rest_framework.metadata import SimpleMetadata
from rest_framework.relations import PrimaryKeyRelatedField

from leasing.models import Contact, Decision, Lease
from users.models import User


class FieldsMetadata(SimpleMetadata):
    """Returns metadata for all the fields and the possible choices in the
    serializer even when the fields are read only.

    Additionally adds decimal_places and max_digits info for DecimalFields."""

    def determine_metadata(self, request, view):
        metadata = super().determine_metadata(request, view)

        serializer = view.get_serializer()
        metadata["fields"] = self.get_serializer_info(serializer)

        return metadata

    def get_field_info(self, field):
        field_info = super().get_field_info(field)

        if isinstance(field, DecimalField):
            field_info['decimal_places'] = field.decimal_places
            field_info['max_digits'] = field.max_digits

        if isinstance(field, PrimaryKeyRelatedField) or isinstance(field, EnumField):
            # TODO: Make configurable
            if hasattr(field, 'queryset') and field.queryset.model in (User, Lease, Contact, Decision):
                return field_info

            field_info['choices'] = [{
                'value': choice_value,
                'display_name': force_text(choice_name, strings_only=True)
            } for choice_value, choice_name in field.choices.items()]

        return field_info
