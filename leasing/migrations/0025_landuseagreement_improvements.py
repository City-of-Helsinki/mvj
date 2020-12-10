# Generated by Django 2.2.13 on 2020-11-26 14:56

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("leasing", "0024_landuseagreement_litigantcontact_as_m2m"),
    ]

    operations = [
        migrations.CreateModel(
            name="LandUseAgreementDecisionConditionType",
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
                ("name", models.CharField(max_length=255, verbose_name="Name")),
            ],
            options={
                "verbose_name": "Land use agreement decision condition type",
                "verbose_name_plural": "Land use agreement decision condition types",
                "ordering": ["name"],
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="LandUseAgreementDecisionType",
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
                ("name", models.CharField(max_length=255, verbose_name="Name")),
            ],
            options={
                "verbose_name": "Land use agreement decision type",
                "verbose_name_plural": "Land use agreement decision types",
                "ordering": ["name"],
                "abstract": False,
            },
        ),
        migrations.RenameModel(
            old_name="LandUseAgreementConditionType",
            new_name="LandUseAgreementConditionFormOfManagement",
        ),
        migrations.RemoveField(
            model_name="landuseagreementcondition", name="description",
        ),
        migrations.RemoveField(model_name="landuseagreementcondition", name="type",),
        migrations.RemoveField(
            model_name="landuseagreementlitigant", name="share_denominator",
        ),
        migrations.RemoveField(
            model_name="landuseagreementlitigant", name="share_numerator",
        ),
        migrations.AddField(
            model_name="landuseagreementcondition",
            name="actualized_area",
            field=models.PositiveIntegerField(
                default=0, verbose_name="Actualized area (f-m2)"
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="landuseagreementcondition",
            name="compensation_pc",
            field=models.PositiveSmallIntegerField(
                default=0, verbose_name="Compensation percent"
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="landuseagreementcondition",
            name="form_of_management",
            field=models.ForeignKey(
                default=0,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="+",
                to="leasing.LandUseAgreementConditionFormOfManagement",
                verbose_name="Form of management",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="landuseagreementcondition",
            name="obligated_area",
            field=models.PositiveIntegerField(
                default=0, verbose_name="Obligated area (f-m2)"
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="landuseagreementcondition",
            name="subvention_amount",
            field=models.PositiveIntegerField(
                default=0, verbose_name="Subvention amount"
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="landuseagreementdecision",
            name="description",
            field=models.TextField(blank=True, null=True, verbose_name="Description"),
        ),
        migrations.AlterField(
            model_name="landuseagreementcondition",
            name="supervised_date",
            field=models.DateField(
                default=datetime.date.today, verbose_name="Supervised date"
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="landuseagreementcondition",
            name="supervision_date",
            field=models.DateField(
                default=datetime.date.today, verbose_name="Supervision date"
            ),
            preserve_default=False,
        ),
        migrations.CreateModel(
            name="LandUseAgreementDecisionCondition",
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
                    "supervision_date",
                    models.DateField(
                        blank=True, null=True, verbose_name="Supervision date"
                    ),
                ),
                (
                    "supervised_date",
                    models.DateField(
                        blank=True, null=True, verbose_name="Supervised date"
                    ),
                ),
                (
                    "description",
                    models.TextField(blank=True, null=True, verbose_name="Description"),
                ),
                (
                    "decision",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="conditions",
                        to="leasing.LandUseAgreementDecision",
                        verbose_name="Decision",
                    ),
                ),
                (
                    "type",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="+",
                        to="leasing.LandUseAgreementDecisionConditionType",
                        verbose_name="Type",
                    ),
                ),
            ],
            options={
                "verbose_name": "Land use agreement decision condition",
                "verbose_name_plural": "Land use agreement decision conditions",
            },
        ),
        migrations.AddField(
            model_name="landuseagreementdecision",
            name="type",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="+",
                to="leasing.LandUseAgreementDecisionType",
                verbose_name="Type",
            ),
        ),
    ]