from django.db.models import ManyToOneRel


class FieldPermissionsAdminMixin:
    """Makes fields readonly or excluded according to the field permissions"""

    def get_readonly_fields(self, request, obj=None):
        from .registry import field_permissions

        if not field_permissions.in_registry(self.model):
            return self.readonly_fields

        result = list(self.readonly_fields) if self.readonly_fields else []

        for field in field_permissions.get_model_fields(self.model):
            field_name = field.name

            # if field_name == 'conditions':
            if isinstance(field, ManyToOneRel):
                continue

            if not request.user.has_perm('{}.view_{}_{}'.format(
                    self.model._meta.app_label, self.model._meta.model_name, field_name)):
                continue

            if not request.user.has_perm('{}.change_{}_{}'.format(
                    self.model._meta.app_label, self.model._meta.model_name, field_name)):
                result.append(field_name)

        return result

    def get_exclude(self, request, obj=None):
        from .registry import field_permissions

        if not field_permissions.in_registry(self.model):
            return self.exclude

        result = list(self.exclude) if self.exclude else []

        for field in field_permissions.get_model_fields(self.model):
            field_name = field.name

            if request.user.has_perm('{}.change_{}_{}'.format(
                    self.model._meta.app_label, self.model._meta.model_name, field_name)):
                continue

            if not request.user.has_perm('{}.view_{}_{}'.format(
                    self.model._meta.app_label, self.model._meta.model_name, field_name)):
                result.append(field_name)

        return result

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)

        if not self.model:
            return fields

        field_names = list(fields)

        for field_name in field_names:
            if not request.user.has_perm('{}.view_{}_{}'.format(
                    self.model._meta.app_label, self.model._meta.model_name, field_name)):
                fields.remove(field_name)

        return fields
