from django.db import migrations, models


def forwards_func(apps, schema_editor):
    PlanUnit = apps.get_model("leasing", "PlanUnit")  # noqa: N806
    for plan_unit in PlanUnit.objects.all():
        plan_unit.master_timestamp = plan_unit.modified_at
        plan_unit.save()

    Plot = apps.get_model("leasing", "Plot")  # noqa: N806
    for plot in Plot.objects.all():
        plot.master_timestamp = plot.modified_at
        plot.save()


class Migration(migrations.Migration):

    dependencies = [
        ("leasing", "0028_modify_land_use_agreement_type"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="leasearea",
            name="is_master",
        ),
        migrations.AddField(
            model_name="planunit",
            name="master_timestamp",
            field=models.DateTimeField(
                blank=True, null=True, verbose_name="Master timestamp"
            ),
        ),
        migrations.AddField(
            model_name="plot",
            name="master_timestamp",
            field=models.DateTimeField(
                blank=True, null=True, verbose_name="Master timestamp"
            ),
        ),
        migrations.RunPython(forwards_func, migrations.RunPython.noop),
    ]
