# Generated by Django 2.2.13 on 2020-10-06 06:38

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("leasing", "0017_add_plot_search_target"),
    ]

    operations = [
        migrations.RunSQL(
            sql="UPDATE leasing_planunit pu SET plan_unit_status = 'pending' from leasing_planunitstate pus WHERE pu.plan_unit_state_id = pus.id and lower(name) like 'vireillä';",
            reverse_sql="UPDATE leasing_planunit pu SET plan_unit_status = 'present' from leasing_planunitstate pus WHERE pu.plan_unit_state_id = pus.id and lower(name) like 'vireillä';",
        )
    ]