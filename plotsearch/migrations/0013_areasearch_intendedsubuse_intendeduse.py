# Generated by Django 3.2.12 on 2022-03-18 09:43

import django.contrib.gis.db.models.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("forms", "0014_add_create_and_open_fields_to_answer"),
        ("plotsearch", "0012_plotsearchtarget_answers"),
    ]

    operations = [
        migrations.CreateModel(
            name="IntendedUse",
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
                "verbose_name": "Area search intended use",
                "verbose_name_plural": "Area search intended uses",
                "ordering": ["name"],
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="IntendedSubUse",
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
                    "intended_use",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="plotsearch.intendeduse",
                    ),
                ),
            ],
            options={
                "verbose_name": "Area search sub intended use",
                "verbose_name_plural": "Area search sub intended uses",
                "ordering": ["intended_use", "name"],
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="AreaSearch",
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
                    "geometry",
                    django.contrib.gis.db.models.fields.MultiPolygonField(
                        blank=True, null=True, srid=4326, verbose_name="Geometry"
                    ),
                ),
                ("description_area", models.TextField()),
                ("description_project", models.TextField()),
                ("description_intended_use", models.TextField()),
                (
                    "start_date",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="Begin at"
                    ),
                ),
                (
                    "end_date",
                    models.DateTimeField(blank=True, null=True, verbose_name="End at"),
                ),
                (
                    "form",
                    models.OneToOneField(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="area_search",
                        to="forms.form",
                    ),
                ),
                (
                    "intended_use",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="plotsearch.intendedsubuse",
                    ),
                ),
            ],
        ),
    ]
