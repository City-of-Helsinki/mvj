from django.apps import AppConfig
from django.db.models.signals import post_migrate

from .receivers import create_permissions


class FieldPermissionsConfig(AppConfig):
    name = 'field_permissions'

    def ready(self):
        post_migrate.connect(create_permissions, dispatch_uid="field_permissions.management.create_permissions")
