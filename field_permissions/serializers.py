class FieldPermissionsSerializerMixin:
    """Change serializer fields according to the field permissions

    Makes sure that the fields the user doesn't have permission to
    are removed and the fields with only view permission are marked
    read only.

    The fields cannot be modified in __init__ because the context
    (including request) is not available when nested serializers are
    initialized in the parent serializer.
    """

    def modify_fields_by_field_permissions(self):
        if 'request' not in self.context:
            return

        model = self.Meta.model

        user = self.context['request'].user

        field_names = list(self.fields)

        for field_name in field_names:
            if user.has_perm('{}.change_{}_{}'.format(model._meta.app_label, model._meta.model_name, field_name)):
                continue

            if user.has_perm('{}.view_{}_{}'.format(model._meta.app_label, model._meta.model_name, field_name)):
                self._fields[field_name].read_only = True
            else:
                del self._fields[field_name]

    def to_representation(self, instance):
        self.modify_fields_by_field_permissions()

        return super().to_representation(instance)
