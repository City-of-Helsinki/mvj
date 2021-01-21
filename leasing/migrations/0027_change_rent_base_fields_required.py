import enumfields.fields
from django.db import migrations, models

import leasing.enums


def forwards_func(apps, schema_editor):
    ContractRent = apps.get_model("leasing", "ContractRent")  # noqa: N806

    contract_rents_with_missing_data_qs = ContractRent.objects.exclude(
        base_amount__isnull=False
    ) | ContractRent.objects.exclude(base_amount_period__isnull=False)

    for contract_rent in contract_rents_with_missing_data_qs:
        if not contract_rent.base_amount:
            contract_rent.base_amount = contract_rent.amount
        if not contract_rent.base_amount_period:
            contract_rent.base_amount_period = contract_rent.period
        contract_rent.save()


class Migration(migrations.Migration):

    dependencies = [
        ("leasing", "0026_land_use_agreement_estate_remove_unique"),
    ]

    operations = [
        migrations.RunPython(forwards_func, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="contractrent",
            name="base_amount",
            field=models.DecimalField(
                decimal_places=2, max_digits=10, verbose_name="Base amount"
            ),
        ),
        migrations.AlterField(
            model_name="contractrent",
            name="base_amount_period",
            field=enumfields.fields.EnumField(
                enum=leasing.enums.PeriodType,
                max_length=30,
                verbose_name="Base amount period",
            ),
        ),
    ]
