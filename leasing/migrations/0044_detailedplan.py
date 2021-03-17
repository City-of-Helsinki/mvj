import enumfields.fields
from django.db import migrations, models

import leasing.enums


class Migration(migrations.Migration):

    dependencies = [
        ("leasing", "0043_change_management_selectable_landuseagreement"),
    ]

    operations = [
        migrations.CreateModel(
            name="DetailedPlan",
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
                (
                    "identifier",
                    models.CharField(max_length=45, verbose_name="Identifier"),
                ),
                (
                    "acceptor",
                    models.CharField(
                        blank=True, max_length=15, verbose_name="Accepter"
                    ),
                ),
                (
                    "detailed_plan_class",
                    enumfields.fields.EnumField(
                        blank=True,
                        enum=leasing.enums.DetailedPlanClass,
                        max_length=30,
                        null=True,
                        verbose_name="Class",
                    ),
                ),
                (
                    "diary_number",
                    models.CharField(
                        blank=True, max_length=45, verbose_name="Diary number"
                    ),
                ),
                (
                    "plan_stage",
                    models.CharField(
                        blank=True, max_length=255, verbose_name="Plan stage"
                    ),
                ),
                (
                    "lawfulness_date",
                    models.DateField(
                        blank=True,
                        max_length=45,
                        null=True,
                        verbose_name="Lawfulness date",
                    ),
                ),
            ],
            options={
                "verbose_name": "Detailed plan",
                "verbose_name_plural": "Detailed plans",
            },
        ),
    ]
