# Generated by Django 3.2.18 on 2023-06-21 08:18

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ("plotsearch", "0024_rename_intendeduse_areasearchintendeduse"),
    ]

    operations = [
        migrations.CreateModel(
            name="DirectReservationLink",
            fields=[
                (
                    "uuid",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("targets", models.ManyToManyField(to="plotsearch.PlotSearchTarget")),
            ],
        ),
    ]
