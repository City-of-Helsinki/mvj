# Generated by Django 3.2.18 on 2024-02-23 09:48

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("leasing", "0071_lease_internal_order"),
        ("plotsearch", "0035_alter_plotsearch_preparers"),
    ]

    operations = [
        migrations.AddField(
            model_name="areasearch",
            name="service_unit",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to="leasing.serviceunit",
            ),
        ),
    ]