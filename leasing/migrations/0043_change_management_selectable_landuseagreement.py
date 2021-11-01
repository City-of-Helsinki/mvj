import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("leasing", "0042_change_definition_null_landuseagreement"),
    ]

    operations = [
        migrations.AlterField(
            model_name="landuseagreementcompensationsunitprice",
            name="management",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="+",
                to="leasing.LandUseAgreementConditionFormOfManagement",
                verbose_name="Management",
            ),
        ),
    ]
