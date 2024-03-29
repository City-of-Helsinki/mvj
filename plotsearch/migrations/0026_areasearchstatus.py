# Generated by Django 3.2.13 on 2023-07-26 07:39

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import enumfields.fields
import plotsearch.enums


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("plotsearch", "0025_directreservationlink"),
    ]

    operations = [
        migrations.CreateModel(
            name="AreaSearchStatus",
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
                    "decline_reason",
                    enumfields.fields.EnumField(
                        blank=True,
                        enum=plotsearch.enums.DeclineReason,
                        max_length=30,
                        null=True,
                    ),
                ),
                ("preparer_note", models.TextField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name="AreaSearchStatusNote",
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
                ("time_stamp", models.DateTimeField(auto_created=True)),
                ("note", models.TextField()),
                (
                    "area_search_status",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="status_notes",
                        to="plotsearch.areasearchstatus",
                    ),
                ),
                (
                    "preparer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="areasearch",
            name="area_search_status",
            field=models.OneToOneField(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="area_search",
                to="plotsearch.areasearchstatus",
            ),
        ),
    ]
