from collections import defaultdict

from django.apps import apps
from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand

from batchrun.permissions import BATCHRUN_GROUP_MODEL_PERMISSIONS
from credit_integration.permissions import CREDIT_INTEGRATION_GROUP_MODEL_PERMISSIONS
from forms.permissions import FORMS_GROUP_MODEL_PERMISSIONS
from leasing.permissions import LEASING_GROUP_MODEL_PERMISSIONS
from plotsearch.permissions import PLOTSEARCH_GROUP_MODEL_PERMISSIONS
from users.permissions import USERS_GROUP_MODEL_PERMISSIONS

APP_LABELS = (
    "batchrun",
    "credit_integration",
    "forms",
    "leasing",
    "plotsearch",
    "users",
)

PERMISSION_TYPES = ("view", "add", "change", "delete")

DEFAULT_MODEL_PERMS = {
    "credit_integration": CREDIT_INTEGRATION_GROUP_MODEL_PERMISSIONS,
    "leasing": LEASING_GROUP_MODEL_PERMISSIONS,
    "users": USERS_GROUP_MODEL_PERMISSIONS,
    "batchrun": BATCHRUN_GROUP_MODEL_PERMISSIONS,
    "plotsearch": PLOTSEARCH_GROUP_MODEL_PERMISSIONS,
    "forms": FORMS_GROUP_MODEL_PERMISSIONS,
}


class Command(BaseCommand):
    help = "Sets predefined model permissions for the predefined MVJ groups"

    def handle(self, *args, **options):  # NOQA
        groups = {group.id: group for group in Group.objects.all()}
        permissions = {
            (permission.content_type.app_label, permission.codename): permission
            for permission in Permission.objects.select_related("content_type")
        }

        all_model_permissions = []
        group_permissions = []

        for app_name in APP_LABELS:
            default_model_perms = DEFAULT_MODEL_PERMS[app_name]
            for model in apps.get_app_config(app_name).get_models(
                include_auto_created=True
            ):
                app_label = model._meta.app_label
                model_name = model._meta.model_name

                if model not in default_model_perms:
                    self.stdout.write(
                        'Model "{}" not in {}.GROUP_MODEL_PERMISSIONS. Skipping.'.format(
                            model_name,
                            app_name,
                        )
                    )
                    continue

                for permission_type in PERMISSION_TYPES:
                    all_model_permissions.append(
                        permissions[
                            (app_label, "{}_{}".format(permission_type, model_name))
                        ]
                    )

                for custom_model_permission_name, desc in model._meta.permissions:
                    all_model_permissions.append(
                        permissions[(app_label, custom_model_permission_name)]
                    )

                for group_id, permission_types in default_model_perms[model].items():
                    if not permission_types:
                        continue

                    for permission_type in permission_types:
                        if permission_type in PERMISSION_TYPES:
                            permission_name = "{}_{}".format(
                                permission_type, model_name
                            )
                        elif (app_label, permission_type) in permissions:
                            permission_name = permission_type
                        else:
                            permission_name = "{}_{}".format(
                                permission_type, model_name
                            )

                        permission = permissions[(app_label, permission_name)]

                        group_permissions.append(
                            Group.permissions.through(
                                group=groups[group_id], permission=permission
                            )
                        )

        # Delete existing group permissions from the pre-defined groups
        mvj_groups = [grp for grp in groups.values() if grp.id in range(1, 8)]
        Group.permissions.through.objects.filter(
            group__in=mvj_groups, permission__in=all_model_permissions
        ).delete()

        # Save the desired field permissions for the groups
        Group.permissions.through.objects.bulk_create(group_permissions)

        # Logging
        permissions_by_group = defaultdict(list)
        for group_permission in group_permissions:
            permissions_by_group[group_permission.group.name].append(
                group_permission.permission.codename
            )
        for group_name, permissions in permissions_by_group.items():
            self.stdout.write(
                f'Added model permissions for group "{group_name}": {", ".join(permissions)}'
            )
