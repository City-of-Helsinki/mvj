# Manually created
# Migrates arbitrarily filled collateral other_type data into description.
# Field is removed in the next migration, and replaced with more specific fields.
from django.db import migrations


def migrate_other_type_to_note(apps, schema_editor):
    collateral_model = apps.get_model("leasing", "Collateral")
    for collateral in collateral_model.objects.exclude(other_type__isnull=True):
        if collateral.note:
            collateral.note = collateral.note + " \n" + collateral.other_type
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
