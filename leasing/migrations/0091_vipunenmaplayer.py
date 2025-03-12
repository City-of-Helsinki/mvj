# Generated by Django 4.2.19 on 2025-03-12 13:11

from django.db import migrations, models
import django.db.models.deletion
import leasing.models.map_layers


class Migration(migrations.Migration):

    dependencies = [
        ("leasing", "0090_alter_leasearea_options"),
    ]

    operations = [
        migrations.CreateModel(
            name="VipunenMapLayer",
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
                ("order_in_parent", models.IntegerField(blank=True, null=True)),
                ("name_fi", models.CharField(max_length=255)),
                ("name_sv", models.CharField(blank=True, max_length=255, null=True)),
                ("name_en", models.CharField(blank=True, max_length=255, null=True)),
                ("keywords", models.CharField(blank=True, max_length=255, null=True)),
                (
                    "hex_color",
                    models.CharField(
                        blank=True,
                        max_length=7,
                        null=True,
                        validators=[leasing.models.map_layers.HexColorValidator()],
                    ),
                ),
                (
                    "intended_use",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="map_layers",
                        to="leasing.intendeduse",
                    ),
                ),
                (
                    "lease_type",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="map_layers",
                        to="leasing.leasetype",
                    ),
                ),
                (
                    "parent",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="children",
                        to="leasing.vipunenmaplayer",
                    ),
                ),
            ],
            options={
                "permissions": [
                    (
                        "export_api_vipunen_map_layer",
                        "Can access export API vipunen map layer",
                    )
                ],
            },
        ),
    ]
