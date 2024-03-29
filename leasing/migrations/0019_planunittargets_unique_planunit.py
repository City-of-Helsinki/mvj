# Generated by Django 2.2.13 on 2020-10-14 11:45

import django.db.models.deletion
from django.db import migrations, models


def forwards_func(apps, schema_editor):
    PlotSearchTarget = apps.get_model("leasing", "PlotSearchTarget")
    PlotSearchTarget.objects.all().delete()


def reverse_func(apps, schema_editor):
    pass


# noqa: F401


class Migration(migrations.Migration):

    dependencies = [
        ("leasing", "0018_transform_plan_unit_pending"),
    ]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
        migrations.AlterField(
            model_name="plotsearchtarget",
            name="plan_unit",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE, to="leasing.PlanUnit"
            ),
        ),
    ]
