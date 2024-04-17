# Generated by Django 3.2.13 on 2023-01-13 11:16

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        (
            "leasing",
            "0055_remove_application_leases",
        ),
    ]

    operations = [
        migrations.AddField(
            model_name="usagedistribution",
            name="plan_unit",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="usage_distributions",
                to="leasing.planunit",
            ),
        ),
        migrations.AlterField(
            model_name="usagedistribution",
            name="custom_detailed_plan",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="usage_distributions",
                to="leasing.customdetailedplan",
            ),
        ),
    ]
