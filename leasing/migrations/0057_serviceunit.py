# Generated by Django 3.2.9 on 2021-12-08 15:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("leasing", "0056_attach_usage_distribution_to_plan_unit"),
    ]

    operations = [
        migrations.CreateModel(
            name="ServiceUnit",
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
                ("deleted", models.DateTimeField(editable=False, null=True)),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="Time created"
                    ),
                ),
                (
                    "modified_at",
                    models.DateTimeField(auto_now=True, verbose_name="Time modified"),
                ),
                ("name", models.CharField(max_length=255, verbose_name="Name")),
                (
                    "description",
                    models.TextField(blank=True, null=True, verbose_name="Description"),
                ),
                (
                    "laske_sender_id",
                    models.CharField(max_length=255, verbose_name="Sender ID in Laske"),
                ),
                (
                    "laske_import_id",
                    models.CharField(max_length=255, verbose_name="Import ID in Laske"),
                ),
                (
                    "laske_sales_org",
                    models.CharField(
                        max_length=255, verbose_name="Sales Organisation in Laske"
                    ),
                ),
            ],
            options={
                "verbose_name": "Service unit",
                "verbose_name_plural": "Service units",
            },
        ),
    ]
