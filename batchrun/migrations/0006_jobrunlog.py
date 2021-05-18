import django.contrib.postgres.fields.jsonb
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("batchrun", "0005_logentry_meta"),
    ]

    operations = [
        migrations.CreateModel(
            name="JobRunLog",
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
                ("content", models.TextField(blank=True, verbose_name="content")),
                (
                    "entry_data",
                    django.contrib.postgres.fields.jsonb.JSONField(
                        blank=True,
                        help_text=(
                            "Data that defines the location, timestamp and "
                            "kind (stdout or stderr) of each log entry within "
                            "the whole log content."
                        ),
                        null=True,
                        verbose_name="log entry metadata",
                    ),
                ),
                (
                    "start",
                    models.DateTimeField(
                        db_index=True, verbose_name="timestamp of the first entry"
                    ),
                ),
                (
                    "end",
                    models.DateTimeField(
                        db_index=True, verbose_name="timestamp of the last entry"
                    ),
                ),
                (
                    "entry_count",
                    models.IntegerField(verbose_name="total count of entries"),
                ),
                (
                    "error_count",
                    models.IntegerField(verbose_name="count of error entries"),
                ),
                (
                    "run",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="log",
                        to="batchrun.JobRun",
                        verbose_name="run",
                    ),
                ),
            ],
            options={
                "verbose_name": "log",
                "verbose_name_plural": "logs",
                "ordering": ("-start",),
            },
        ),
    ]
