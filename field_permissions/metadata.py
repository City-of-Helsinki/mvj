from collections import OrderedDict

from rest_framework import serializers


class FieldPermissionsMetadataMixin:
    """Removes fields from the serializer that the user doesn't have permission to
    when determining metadata."""

    def get_serializer_info(self, serializer):
        """
        Given an instance of a serializer, return a dictionary of metadata
        about its fields.
        """
        if hasattr(serializer, 'child'):
            # If this is a `ListSerializer` then we want to examine the
            # underlying child serializer instance instead.
            serializer = serializer.child

        # Remove the fields the user doesn't have access to
        if hasattr(serializer, 'modify_fields_by_field_permissions'):
            serializer.modify_fields_by_field_permissions()

        return OrderedDict(
            [(field_name, self.get_field_info(field)) for field_name, field in serializer.fields.items() if
                not isinstance(field, serializers.HiddenField)])
