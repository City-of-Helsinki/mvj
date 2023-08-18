# Generated by Django 2.2.13 on 2021-02-24 15:18

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("leasing", "0035_modify_landuseagreementcompensations"),
    ]

    operations = [
        migrations.CreateModel(
            name="LandUseAgreementCompensationsUnitPrice",
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
                (
                    "usage",
                    models.CharField(blank=True, max_length=255, verbose_name="Usage"),
                ),
                (
                    "management",
                    models.CharField(
                        blank=True, max_length=255, verbose_name="Management"
                    ),
                ),
                (
                    "protected",
                    models.CharField(
                        blank=True, max_length=255, verbose_name="Protected"
                    ),
                ),
                (
                    "area",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=12,
                        null=True,
                        verbose_name="Area",
                    ),
                ),
                (
                    "unit_value",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=12,
                        null=True,
                        verbose_name="Unit value",
                    ),
                ),
                (
                    "discount",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=12,
                        null=True,
                        verbose_name="Discount",
                    ),
                ),
                (
                    "used_price",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=12,
                        null=True,
                        verbose_name="Used price",
                    ),
                ),
                (
                    "compensations",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="unit_prices_used_in_calculation",
                        to="leasing.LandUseAgreementCompensations",
                    ),
                ),
            ],
            options={"ordering": ["name"], "abstract": False, },
        ),
    ]
