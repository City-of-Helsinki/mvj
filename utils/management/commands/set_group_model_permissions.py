from collections import defaultdict
from typing import Any

from django.apps import apps
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.db.models import Model

from batchrun.permissions import BATCHRUN_GROUP_MODEL_PERMISSIONS
from credit_integration.permissions import CREDIT_INTEGRATION_GROUP_MODEL_PERMISSIONS
from forms.permissions import FORMS_GROUP_MODEL_PERMISSIONS
from leasing.permissions import LEASING_GROUP_MODEL_PERMISSIONS
from plotsearch.permissions import PLOTSEARCH_GROUP_MODEL_PERMISSIONS
from users.permissions import USERS_GROUP_MODEL_PERMISSIONS
from utils.group_permissions import MANAGED_USER_GROUP_ID_RANGE

PERMISSION_TYPES = ("view", "add", "change", "delete")

APP_PERMISSION_CONFIGS = {
    "credit_integration": CREDIT_INTEGRATION_GROUP_MODEL_PERMISSIONS,
    "leasing": LEASING_GROUP_MODEL_PERMISSIONS,
    "users": USERS_GROUP_MODEL_PERMISSIONS,
    "batchrun": BATCHRUN_GROUP_MODEL_PERMISSIONS,
    "plotsearch": PLOTSEARCH_GROUP_MODEL_PERMISSIONS,
    "forms": FORMS_GROUP_MODEL_PERMISSIONS,
}

APP_LABELS = tuple(APP_PERMISSION_CONFIGS.keys())


class Command(BaseCommand):
    help = "Sets predefined model permissions for the predefined MVJ groups"

    def handle(self, *args: Any, **options: Any) -> None:
        groups = {group.id: group for group in Group.objects.all()}

        all_model_permissions = []
        all_group_permissions = []

        for app_name in APP_LABELS:
            app_permission_config = APP_PERMISSION_CONFIGS[app_name]
            for model in apps.get_app_config(app_name).get_models(
                include_auto_created=True
            ):
                model_name = model._meta.model_name

                if model not in app_permission_config:
                    self.stdout.write(
                        'Model "{}" not in {}.GROUP_MODEL_PERMISSIONS. Skipping.'.format(
                            model_name,
                            app_name,
                        )
                    )
                    continue

                permissions_by_codename = get_permissions_by_codename(model)
                model_permissions = get_model_permissions(
                    model, permissions_by_codename
                )
                all_model_permissions.extend(model_permissions)

                group_permissions = get_group_permissions(
                    groups,
                    model,
                    app_permission_config[model]["model"],
                    permissions_by_codename,
                )
                all_group_permissions.extend(group_permissions)

        # Delete existing group permissions from the pre-defined groups
        mvj_groups = [
            grp for grp in groups.values() if grp.id in MANAGED_USER_GROUP_ID_RANGE
        ]
        Group.permissions.through.objects.filter(
            group__in=mvj_groups, permission__in=all_model_permissions
        ).delete()

        # Save the desired field permissions for the groups
        Group.permissions.through.objects.bulk_create(all_group_permissions)

        log_group_permissions(self, all_group_permissions)


def get_permissions_by_codename(model: type[Model]) -> dict[str, Permission]:
    content_type = ContentType.objects.get_for_model(model, for_concrete_model=False)
    return {
        permission.codename: permission
        for permission in Permission.objects.filter(content_type=content_type)
    }


def get_model_permissions(
    model: type[Model], permissions_by_codename: dict[str, Permission]
) -> list[Permission]:
    model_name = model._meta.model_name
    standard_permissions = [
        permissions_by_codename[f"{permission_type}_{model_name}"]
        for permission_type in PERMISSION_TYPES
    ]
    custom_permissions = [
        permissions_by_codename[permission_name]
        for permission_name, _ in model._meta.permissions
    ]
    return standard_permissions + custom_permissions


def get_permission_name(
    permission_type: str,
    model_name: str,
    permissions_by_codename: dict[str, Permission],
) -> str:
    if (
        permission_type in PERMISSION_TYPES
        or permission_type not in permissions_by_codename
    ):
        return f"{permission_type}_{model_name}"
    return permission_type


def get_group_permissions(
    groups: dict[int, Group],
    model: type[Model],
    configured_permissions: dict[int, list[str]],
    permissions_by_codename: dict[str, Permission],
) -> list[Any]:
    model_name = model._meta.model_name
    assert model_name is not None
    group_permissions = []

    for group_id, permission_types in configured_permissions.items():
        if not permission_types:
            continue

        for permission_type in permission_types:
            permission_name = get_permission_name(
                permission_type, model_name, permissions_by_codename
            )
            group_permissions.append(
                Group.permissions.through(
                    group=groups[group_id],
                    permission=permissions_by_codename[permission_name],
                )
            )

    return group_permissions


def log_group_permissions(command: Command, group_permissions: list[Any]) -> None:
    permissions_by_group = defaultdict(list)
    for group_permission in group_permissions:
        permissions_by_group[group_permission.group.name].append(
            group_permission.permission.codename
        )

    for group_name, permissions in permissions_by_group.items():
        command.stdout.write(
            f'Added model permissions for group "{group_name}": {", ".join(permissions)}'
        )
