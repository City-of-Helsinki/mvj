# Generated by Django 3.2.13 on 2022-09-28 06:43

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("leasing", "0052_update_customdetailedplan_fields"),
        (
            "plotsearch",
            "0017_add_target_selection_created_mofied_fields_alter_preparer_field",
        ),
    ]

    operations = [
        migrations.AddField(
            model_name="targetinfolink",
            name="custom_detailed_plan",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="info_links",
                to="leasing.customdetailedplan",
            ),
        ),
        migrations.AlterField(
            model_name="targetinfolink",
            name="plot_search_target",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="info_links",
                to="plotsearch.plotsearchtarget",
            ),
        ),
    ]
