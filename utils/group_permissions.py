from enum import IntEnum
from typing import NotRequired, TypeAlias, TypedDict

from django.db.models import Model


class UserGroup(IntEnum):
    SELAILIJA = 1
    VALMISTELIJA = 2
    SOPIMUSVALMISTELIJA = 3
    SYOTTAJA = 4
    PERINTALAKIMIES = 5
    LASKUTTAJA = 6
    PAAKAYTTAJA = 7


UG = UserGroup

MANAGED_USER_GROUP_ID_RANGE = [
    group.value for group in UserGroup
]  # These groups have their permissions managed with permissions management commands.


PermissionNames: TypeAlias = tuple[str, ...] | None
ModelGroupPermissions: TypeAlias = dict[UserGroup, PermissionNames]
FieldGroupPermissions: TypeAlias = dict[UserGroup, str | None]
FieldPermissions: TypeAlias = dict[str, FieldGroupPermissions]


class ModelPermissionConfiguration(TypedDict):
    """Configured model- and field-level permissions for one Django model."""

    model: ModelGroupPermissions  # Standard django model permissions
    fields: NotRequired[
        FieldPermissions
    ]  # Custom field_permissions app definitions for fine-grained control


GroupModelPermissions: TypeAlias = dict[type[Model], ModelPermissionConfiguration]
