import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("leasing", "0041_landuseagreementidentifier_identifier"),
    ]

    operations = [
        migrations.AlterField(
            model_name="landuseagreement",
            name="definition",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="+",
                to="leasing.LandUseAgreementDefinition",
                verbose_name="Land use agreement definition",
            ),
        ),
    ]
