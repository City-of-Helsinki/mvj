from field_permissions.registry import field_permissions


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

        if not field_permissions.in_registry(model):
            return

        user = self.context['request'].user
        field_names = list(self.fields)
        excluded_field_names = field_permissions.get_exclude_fields_for(model)

        for field_name in field_names:
            permission_check_field_name = field_name

            if hasattr(self, 'override_permission_check_field_name'):
                permission_check_field_name = self.override_permission_check_field_name(field_name)

            if permission_check_field_name in excluded_field_names:
                continue

            if user.has_perm('{}.change_{}_{}'.format(model._meta.app_label, model._meta.model_name,
                                                      permission_check_field_name)):
                continue

            if user.has_perm('{}.view_{}_{}'.format(model._meta.app_label, model._meta.model_name,
                                                    permission_check_field_name)):
                self.fields[field_name].read_only = True
            else:
                del self.fields[field_name]

    def to_representation(self, instance):
        self.modify_fields_by_field_permissions()

        return super().to_representation(instance)
