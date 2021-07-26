import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("batchrun", "0005_logentry_kind_3"),
    ]

    operations = [
        migrations.RemoveField(model_name="jobrun", name="deleted",),
        migrations.RemoveField(model_name="jobrunlogentry", name="deleted",),
        migrations.RemoveField(model_name="scheduledjob", name="deleted",),
        migrations.AlterField(
            model_name="jobrunlogentry",
            name="run",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="log_entries",
                to="batchrun.JobRun",
                verbose_name="run",
            ),
        ),
    ]
