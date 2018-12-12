from django.db.models import ManyToOneRel, Model

FIELD_PERMISSION_TYPES = ['view', 'change']


class FieldPermissionsModelRegistry(object):
    def __init__(self):
        self._registry = {}

    def register(self, cls, include_fields=None, exclude_fields=None):
        if not issubclass(cls, Model):
            raise TypeError("cls should be a Model")

        if include_fields is None:
            include_fields = '__all__'

        if exclude_fields is None:
            exclude_fields = []

        self._registry[cls] = {
            'include_fields': include_fields,
            'exclude_fields': exclude_fields,
        }

    def in_registry(self, klass):
        model_name = klass._meta.model_name

        return model_name in [klass._meta.model_name for klass in self._registry.keys()]

    def get_include_fields_for(self, klass):
        model_name = klass._meta.model_name

        for klass, conf in self._registry.items():
            if klass._meta.model_name == model_name:
                return conf['include_fields']

        return []

    def get_exclude_fields_for(self, klass):
        model_name = klass._meta.model_name

        for klass, conf in self._registry.items():
            if klass._meta.model_name == model_name:
                return conf['exclude_fields']

        return []

    def get_models(self):
        return self._registry.keys()

    def get_model_fields(self, klass):
        opts = klass._meta
        include_fields = self.get_include_fields_for(klass)
        exclude_fields = self.get_exclude_fields_for(klass)

        fields = []
        for field in opts.get_fields(include_parents=True):
            if include_fields != '__all__' and field.name not in include_fields:
                continue
            if field.name in exclude_fields:
                continue

            fields.append(field)

        return fields

    def get_field_permissions_for_model(self, klass):
        opts = klass._meta
        include_fields = self.get_include_fields_for(klass)
        exclude_fields = self.get_exclude_fields_for(klass)

        perms = []
        for field in opts.get_fields(include_parents=True):
            if include_fields != '__all__' and field.name not in include_fields:
                continue
            if field.name in exclude_fields:
                continue

            for permission_type in FIELD_PERMISSION_TYPES:
                field_name = field.name
                verbose_field_name = field.name

                if hasattr(field, 'verbose_name'):
                    verbose_field_name = field.verbose_name
                elif isinstance(field, ManyToOneRel):
                    if field.related_name:
                        verbose_field_name = field.related_model._meta.verbose_name_plural
                    else:
                        # If related_name is not set, add permission for the default [field name]_set field
                        field_name = field_name + '_set'
                        verbose_field_name = field_name + ' set'

                perms.append(
                    (
                        '{}_{}_{}'.format(permission_type, opts.model_name, field_name),
                        'Can {} field {} in {}'.format(permission_type, verbose_field_name.lower(), opts.verbose_name)
                    )
                )

        return perms


field_permissions = FieldPermissionsModelRegistry()
