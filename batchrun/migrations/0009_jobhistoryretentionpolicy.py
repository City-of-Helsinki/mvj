import datetime

import django.db.models.deletion
from django.db import migrations, models

from ..models import _get_default_job_history_retention_policy_pk


class Migration(migrations.Migration):

    dependencies = [
        ("batchrun", "0008_jobrunlog"),
    ]

    operations = [
        migrations.CreateModel(
            name="JobHistoryRetentionPolicy",
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
                    "identifier",
                    models.CharField(
                        max_length=30, unique=True, verbose_name="identifier"
                    ),
                ),
                (
                    "compact_logs_delay",
                    models.DurationField(
                        default=datetime.timedelta(14),
                        help_text=(
                            "Days to wait before compacting log entries. "
                            "Calculated from the start time of the job. "
                            "Compacting log entries means that the individual "
                            "log entries are concatenated to a single string and the "
                            "original entries are deleted. This allows PostgreSQL "
                            'to compress the log contents (check "TOAST" from '
                            "PostgreSQL documentation). The metadata information about "
                            "the log entry kinds (stdout/stderr) and timestamps are "
                            "stored separately so that the original contents of the log "
                            "entries are still recoverable."
                        ),
                        verbose_name="log compacting delay",
                    ),
                ),
                (
                    "delete_logs_delay",
                    models.DurationField(
                        default=datetime.timedelta(1461),
                        help_text=(
                            "Days to wait before deleting logs. "
                            "Calculated from the start time of the job."
                        ),
                        verbose_name="log deleting delay",
                    ),
                ),
                (
                    "delete_run_delay",
                    models.DurationField(
                        default=datetime.timedelta(3652),
                        help_text=(
                            "Days to wait before deleting all inforomation about the run. "
                            "Calculated from the start time of the job."
                        ),
                        verbose_name="run inforomation deleting delay",
                    ),
                ),
            ],
            options={
                "verbose_name": "job history retention policy",
                "verbose_name_plural": "job history retention policies",
            },
        ),
        migrations.AddField(
            model_name="job",
            name="history_retention_policy",
            field=models.ForeignKey(
                default=_get_default_job_history_retention_policy_pk,
                help_text="Defines how long logs and information about completed runs is preserved.",
                on_delete=django.db.models.deletion.PROTECT,
                to="batchrun.JobHistoryRetentionPolicy",
                verbose_name="history retention policy",
            ),
        ),
    ]
