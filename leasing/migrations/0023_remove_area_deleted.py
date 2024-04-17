# Generated by Django 2.2.13 on 2020-11-03 06:48

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("leasing", "0022_require_plot_search_target_type"),
    ]

    operations = [
        migrations.RunSQL(
            "DELETE FROM leasing_area WHERE deleted IS NOT NULL",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RemoveField(
            model_name="area",
            name="deleted",
        ),
    ]
