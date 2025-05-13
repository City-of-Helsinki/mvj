from django.db import migrations


def delete_inactive_intended_uses_with_service_unit_1(apps, schema_editor):
    """
    Delete all IntendedUse instances where is_active=False and service_unit_id=1

    This is a one-time migration to clean up the database by removing legacy
    MAKE service unit intended uses that are no longer needed.
    """
    IntendedUse = apps.get_model("leasing", "IntendedUse")  # noqa: N806
    inactive_intended_uses = IntendedUse.objects.filter(
        is_active=False, service_unit_id=1
    )
    inactive_intended_uses.delete()


class Migration(migrations.Migration):

    dependencies = [
        ("leasing", "0098_alter_leasebasisofrent_subvention_graduated_percent"),
    ]

    operations = [
        migrations.RunPython(
            delete_inactive_intended_uses_with_service_unit_1, migrations.RunPython.noop
        ),
    ]
