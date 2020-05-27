class FieldPermissionsViewsetMixin:
    def get_serializer(self, *args, **kwargs):
        """
        Modifies the serializer according to the field permissions
        """
        serializer = super().get_serializer(*args, **kwargs)

        if hasattr(serializer, "modify_fields_by_field_permissions"):
            serializer.modify_fields_by_field_permissions()

        return serializer
