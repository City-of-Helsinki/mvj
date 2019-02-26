from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _
from enumfields.drf import EnumField
from rest_framework.fields import ChoiceField, DecimalField
from rest_framework.metadata import SimpleMetadata
from rest_framework.relations import PrimaryKeyRelatedField

from field_permissions.metadata import FieldPermissionsMetadataMixin
from leasing.models import Contact, Decision, Invoice, Lease, LeaseArea
from leasing.models.invoice import InvoiceSet
from leasing.permissions import PerMethodPermission
from users.models import User

ALL_METHODS = {
    'GET': False,
    'OPTIONS': False,
    'HEAD': False,
    'POST': False,
    'PUT': False,
    'PATCH': False,
    'DELETE': False,
}


class FieldsMetadata(FieldPermissionsMetadataMixin, SimpleMetadata):
    """Returns metadata for all the fields and the possible choices in the
    serializer even when the fields are read only.

    Additionally adds decimal_places and max_digits info for DecimalFields."""

    def determine_metadata(self, request, view, serializer=None):
        metadata = super().determine_metadata(request, view)

        if not serializer and hasattr(view, 'get_serializer'):
            serializer = view.get_serializer()

        if serializer:
            metadata["fields"] = self.get_serializer_info(serializer)

            # Determine allowed methods for model views
            if hasattr(serializer, 'Meta') and serializer.Meta.model:

                method_permissions = ALL_METHODS.copy()

                for permission in view.get_permissions():
                    if not hasattr(permission, 'get_required_permissions'):
                        continue

                    for method in method_permissions.keys():
                        perms = permission.get_required_permissions(method, serializer.Meta.model)
                        method_permissions[method] = request.user.has_perms(perms)

                metadata['methods'] = method_permissions

        # Determine methods the user has permission to for custom views
        # and viewsets that are using PerMethodPermission.
        if PerMethodPermission in view.permission_classes:
            permission = PerMethodPermission()
            method_permissions = {}
            for method in view.allowed_methods:
                required_perms = permission.get_required_permissions(method, view)
                method_permissions[method.upper()] = request.user.has_perms(required_perms)

            metadata['methods'] = method_permissions

        return metadata

    def get_field_info(self, field):
        field_info = super().get_field_info(field)

        if isinstance(field, DecimalField):
            field_info['decimal_places'] = field.decimal_places
            field_info['max_digits'] = field.max_digits

        # Kludge for translating language names
        if isinstance(field, ChoiceField) and field.field_name == 'language':
            field_info['choices'] = [{
                'value': choice_value,
                'display_name': _(choice_name).capitalize(),
            } for choice_value, choice_name in field.choices.items()]

            field_info['choices'].sort(key=lambda x: x['display_name'])

        if isinstance(field, PrimaryKeyRelatedField) or isinstance(field, EnumField):
            # TODO: Make configurable
            if hasattr(field, 'queryset') and field.queryset.model in (User, Lease, Contact, Decision, Invoice,
                                                                       InvoiceSet, LeaseArea):
                return field_info

            field_info['choices'] = [{
                'value': choice_value,
                'display_name': force_text(choice_name, strings_only=True)
            } for choice_value, choice_name in field.choices.items()]

        return field_info
