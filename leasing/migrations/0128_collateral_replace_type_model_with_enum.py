# Manually created.
# Converts Collateral "type" NameModel into an enum field.
import enumfields.fields
import leasing.enums
from django.db import migrations, models
import django.db.models.deletion

COLLATERAL_TYPES = {
    1: "mortgage_document",
    2: "financial_guarantee",
    3: "other",
    4: "self_debtor_guarantee",
    5: "pledge_of_funds",
}


def migrate_type_fk_to_enum(apps, schema_editor):
    collateral = apps.get_model("leasing", "Collateral")
    for pk, enum_value in COLLATERAL_TYPES.items():
        collateral.objects.filter(type_id=pk).update(type_enum=enum_value)


COLLATERAL_TYPE_NAMES = {
    1: "Panttikirja",
    2: "Rahavakuus",
    3: "Muu vakuus",
    4: "Omavelkainen takaus",
    5: "Tilivarojen panttaus",
}


def reverse_migrate_type_enum_to_fk(apps, schema_editor):
    collateral = apps.get_model("leasing", "Collateral")
    collateral_type = apps.get_model("leasing", "CollateralType")
    for pk, name in COLLATERAL_TYPE_NAMES.items():
        collateral_type.objects.get_or_create(pk=pk, defaults={"name": name})
    enum_to_pk = {v: k for k, v in COLLATERAL_TYPES.items()}
    for enum_value, pk in enum_to_pk.items():
        collateral.objects.filter(type_enum=enum_value).update(type_id=pk)


class Migration(migrations.Migration):

    dependencies = [
        (
            "leasing",
            "0127_collateral_number_mortgage_document_to_dedicated_field_and_mark_legacy",
        ),
    ]

    operations = [
        migrations.AddField(
            model_name="collateral",
            name="type_enum",
            field=enumfields.fields.EnumField(
                blank=True,
                enum=leasing.enums.CollateralType,
                max_length=255,
                null=True,
                verbose_name="Collateral type",
            ),
        ),
        migrations.AlterField(
            model_name="collateral",
            name="type",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="+",
                to="leasing.CollateralType",
                verbose_name="Collateral type",
            ),
        ),
        migrations.RunPython(
            migrate_type_fk_to_enum,
            reverse_migrate_type_enum_to_fk,
        ),
        migrations.AlterField(
            model_name="collateral",
            name="type_enum",
            field=enumfields.fields.EnumField(
                enum=leasing.enums.CollateralType,
                max_length=255,
                verbose_name="Collateral type",
            ),
        ),
        migrations.RemoveField(
            model_name="collateral",
            name="type",
        ),
        migrations.RenameField(
            model_name="collateral",
            old_name="type_enum",
            new_name="type",
        ),
        migrations.DeleteModel(
            name="CollateralType",
        ),
    ]
