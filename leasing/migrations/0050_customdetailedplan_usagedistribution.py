# Generated by Django 3.2.13 on 2022-07-13 11:26

from django.db import migrations, models
import django.db.models.deletion
import enumfields.fields
import leasing.enums


class Migration(migrations.Migration):

    dependencies = [
        ("leasing", "0049_add_translations"),
    ]

    operations = [
        migrations.CreateModel(
            name="CustomDetailedPlan",
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
                ("identifier", models.CharField(max_length=255)),
                ("rent_build_permission", models.IntegerField()),
                ("area", models.IntegerField()),
                ("section_area", models.IntegerField()),
                (
                    "detailed_plan",
                    models.CharField(
                        blank=True,
                        max_length=255,
                        null=True,
                        verbose_name="Detailed plan identifier",
                    ),
                ),
                (
                    "state",
                    enumfields.fields.EnumField(
                        default="present",
                        enum=leasing.enums.PlanUnitStatus,
                        max_length=30,
                        verbose_name="Plan unit status",
                    ),
                ),
                (
                    "detailed_plan_latest_processing_date",
                    models.DateField(
                        blank=True,
                        null=True,
                        verbose_name="Detailed plan latest processing date",
                    ),
                ),
                (
                    "detailed_plan_latest_processing_date_note",
                    models.TextField(
                        blank=True,
                        null=True,
                        verbose_name="Note for latest processing date",
                    ),
                ),
                (
                    "intended_use",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="leasing.planunitintendeduse",
                    ),
                ),
                (
                    "lease_area",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="custom_detailed_plan",
                        to="leasing.leasearea",
                    ),
                ),
            ],
            options={"abstract": False, },
        ),
        migrations.CreateModel(
            name="UsageDistribution",
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
                ("distribution", models.IntegerField()),
                ("build_permission", models.CharField(max_length=255)),
                ("note", models.TextField()),
                (
                    "custom_detailed_plan",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="usage_distributions",
                        to="leasing.customdetailedplan",
                    ),
                ),
            ],
        ),
    ]
