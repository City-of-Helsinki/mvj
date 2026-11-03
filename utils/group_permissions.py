from typing import NotRequired, TypeAlias, TypedDict

from django.db.models import Model

from utils.enums import AuthGroupId

MANAGED_USER_GROUP_ID_RANGE = [
    group.value for group in AuthGroupId
]  # These groups have their permissions managed with permissions management commands.


PermissionNames: TypeAlias = tuple[str, ...] | None
ModelGroupPermissions: TypeAlias = dict[AuthGroupId, PermissionNames]
FieldGroupPermissions: TypeAlias = dict[AuthGroupId, str | None]
FieldPermissions: TypeAlias = dict[str, FieldGroupPermissions]


class ModelPermissionConfiguration(TypedDict):
    """Configured model- and field-level permissions for one Django model."""

    model: ModelGroupPermissions  # Standard django model permissions
    fields: NotRequired[
        FieldPermissions
    ]  # Custom field_permissions app definitions for fine-grained control


GroupModelPermissions: TypeAlias = dict[type[Model], ModelPermissionConfiguration]
