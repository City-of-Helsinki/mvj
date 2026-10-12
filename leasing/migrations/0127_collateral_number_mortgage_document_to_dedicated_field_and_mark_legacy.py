# Manually created
from django.db import migrations, models


def migrate_number_mortgage_document_to_dedicated_field(apps, schema_editor):
    Collateral = apps.get_model("leasing", "Collateral")
    Collateral.objects.filter(type_id=1, number__isnull=False).update(
        number_mortgage_document=models.F("number"),
        number=None,
    )


def reverse_migrate_number_mortgage_document_to_dedicated_field(apps, schema_editor):
    Collateral = apps.get_model("leasing", "Collateral")
    Collateral.objects.filter(type_id=1, number_mortgage_document__isnull=False).update(
        number=models.F("number_mortgage_document"),
        number_mortgage_document=None,
    )


class Migration(migrations.Migration):

    dependencies = [
        (
            "leasing",
            "0126_remove_collateral_other_type_and_more",
        ),
    ]

    operations = [
        migrations.RunPython(
            migrate_number_mortgage_document_to_dedicated_field,
            reverse_migrate_number_mortgage_document_to_dedicated_field,
        ),
        # Update default collateral version to 2
        migrations.AlterField(
            model_name="collateral",
            name="form_version",
            field=models.IntegerField(
                default=2,
                help_text="Used in the background to determine collateral form validation to ensure backwards compatibility in case of breaking changes.",
                verbose_name="Form version",
            ),
        ),
    ]
