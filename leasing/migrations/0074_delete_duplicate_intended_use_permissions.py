# Manually created

from django.db import migrations


def remove_duplicate_intended_use_permissions(apps, schema_editor):
    """
    Remove duplicate intended use permissions and the related auth group permissions.
    """
    Permission = apps.get_model("auth", "Permission")
    permissions = Permission.objects.filter(
        name__contains="Area search intended use",
        codename__contains="_intendeduse",
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("leasing", "0073_intendeduse_service_unit"),
    ]

    operations = [
        migrations.RunPython(
            code=remove_duplicate_intended_use_permissions,
        ),
    ]
