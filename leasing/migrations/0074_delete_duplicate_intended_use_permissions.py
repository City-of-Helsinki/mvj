# Manually created

from django.db import migrations


def remove_duplicate_intended_use_permissions(apps, schema_editor):
    """
    Remove duplicate intended use permissions and the related auth group permissions.
    """
    permission = apps.get_model("auth", "Permission")

    permission.objects.filter(
        name="Can view Area search intended use",
        codename="view_intendeduse",
    ).delete()

    permission.objects.filter(
        name="Can add Area search intended use",
        codename="add_intendeduse",
    ).delete()

    permission.objects.filter(
        name="Can change Area search intended use",
        codename="change_intendeduse",
    ).delete()

    permission.objects.filter(
        name="Can delete Area search intended use",
        codename="delete_intendeduse",
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
