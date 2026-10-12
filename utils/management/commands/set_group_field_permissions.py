from collections import defaultdict
from typing import Any

from django.apps import apps
from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Model

from batchrun.permissions import BATCHRUN_GROUP_MODEL_PERMISSIONS
from credit_integration.permissions import CREDIT_INTEGRATION_GROUP_MODEL_PERMISSIONS
from forms.permissions import FORMS_GROUP_MODEL_PERMISSIONS
from leasing.permissions import LEASING_GROUP_MODEL_PERMISSIONS
from plotsearch.permissions import PLOTSEARCH_GROUP_MODEL_PERMISSIONS
from users.permissions import USERS_GROUP_MODEL_PERMISSIONS
from utils.group_permissions import (
    MANAGED_USER_GROUP_ID_RANGE,
    FieldGroupPermissions,
    GroupModelPermissions,
)

DEFAULT_FIELD_PERMISSIONS_KEY = "_default"

FIELD_PERMISSION_CONFIGS: tuple[GroupModelPermissions, ...] = (
    BATCHRUN_GROUP_MODEL_PERMISSIONS,
    CREDIT_INTEGRATION_GROUP_MODEL_PERMISSIONS,
    FORMS_GROUP_MODEL_PERMISSIONS,
    LEASING_GROUP_MODEL_PERMISSIONS,
    PLOTSEARCH_GROUP_MODEL_PERMISSIONS,
    USERS_GROUP_MODEL_PERMISSIONS,
)


def get_field_permissions(model: type[Model]) -> dict[str, FieldGroupPermissions]:
    for permission_configs in FIELD_PERMISSION_CONFIGS:
        if model in permission_configs:
            return permission_configs[model].get("fields", {})
    return {}


def get_permissions_for_field(
    field_permissions: dict[str, FieldGroupPermissions], field_name: str
) -> FieldGroupPermissions:
    return {
        **field_permissions.get(DEFAULT_FIELD_PERMISSIONS_KEY, {}),
        **field_permissions.get(field_name, {}),
    }


def get_managed_group_permissions(
    groups: dict[int, Group], permissions: dict[str, Permission]
) -> tuple[list[Any], list[Permission]]:
    from field_permissions.registry import field_permissions

    group_permissions = []
    all_field_permissions = []

    for model in field_permissions.get_models():
        model_name = model._meta.model_name
        assert model_name is not None
        configured_field_permissions = get_field_permissions(model)

        for codename, _ in sorted(
            field_permissions.get_field_permissions_for_model(model)
        ):
            try:
                all_field_permissions.append(permissions[codename])
            except KeyError:
                raise CommandError(
                    f'"{codename}" field permission is missing. '
                    "Please run migrate to create the missing permissions."
                )

            if codename.startswith("change_"):
                continue

            field_name = codename.removeprefix(f"view_{model_name}_")
            for group_id, permission_type in get_permissions_for_field(
                configured_field_permissions, field_name
            ).items():
                if permission_type:
                    permission_name = f"{permission_type}_{model_name}_{field_name}"
                    group_permissions.append(
                        Group.permissions.through(
                            group=groups[group_id],
                            permission=permissions[permission_name],
                        )
                    )

    return group_permissions, all_field_permissions


def log_group_permissions(command: BaseCommand, group_permissions: list[Any]) -> None:
    permissions_by_group = defaultdict(list)
    for group_permission in group_permissions:
        permissions_by_group[group_permission.group.name].append(
            group_permission.permission.codename
        )
    for group_name, permission_names in permissions_by_group.items():
        command.stdout.write(
            f'Added field permissions for group "{group_name}": '
            f'{", ".join(permission_names)}'
        )


class Command(BaseCommand):
    help = "Sets predefined field permissions for the predefined MVJ groups"

    def handle(self, *args: Any, **options: Any) -> None:
        if not apps.is_installed("field_permissions"):
            raise CommandError(
                'App "field_permissions" must be installed to use this command.'
            )

        groups = Group.objects.in_bulk()
        permissions = {
            permission.codename: permission for permission in Permission.objects.all()
        }
        group_permissions, all_field_permissions = get_managed_group_permissions(
            groups, permissions
        )

        managed_groups = [
            group
            for group in groups.values()
            if group.id in MANAGED_USER_GROUP_ID_RANGE
        ]
        Group.permissions.through.objects.filter(
            group__in=managed_groups, permission__in=all_field_permissions
        ).delete()
        Group.permissions.through.objects.bulk_create(group_permissions)

        log_group_permissions(self, group_permissions)
