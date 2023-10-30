# Generated by Django 3.2.13 on 2022-06-27 12:15

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("leasing", "0065_service_unit_invoice_number_sequence"),
    ]

    operations = [
        migrations.CreateModel(
            name="ServiceUnitGroupMapping",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "group",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="service_units",
                        to="auth.group",
                    ),
                ),
                (
                    "service_unit",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="groups",
                        to="leasing.serviceunit",
                    ),
                ),
            ],
            options={
                "verbose_name": "Service unit group mapping",
                "verbose_name_plural": "Service unit group mappings",
                "unique_together": {("group", "service_unit")},
            },
        ),
    ]