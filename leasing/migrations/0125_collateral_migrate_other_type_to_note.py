# Manually created
from django.db import migrations


def migrate_other_type_to_note(apps, schema_editor):
    Collateral = apps.get_model("leasing", "Collateral")
    for collateral in Collateral.objects.exclude(other_type__isnull=True):
        if collateral.note:
            collateral.note = collateral.note + "\n" + collateral.other_type
        else:
            collateral.note = collateral.other_type
        collateral.save()


class Migration(migrations.Migration):

    dependencies = [
        ("leasing", "0124_fix_decision_type_typo"),
    ]

    operations = [
        migrations.RunPython(migrate_other_type_to_note, migrations.RunPython.noop),
    ]
