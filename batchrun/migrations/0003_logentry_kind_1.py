from django.db import migrations, models
from enumfields.fields import EnumIntegerField

from ..enums import LogEntryKind


class Migration(migrations.Migration):
    dependencies = [
        ("batchrun", "0002_add_safedelete_to_logs"),
    ]

    operations = [
        migrations.AlterField(  # (*) Add default value to "kind" field
            model_name="jobrunlogentry",
            name="kind",
            field=models.CharField(max_length=30, default="stdout"),
        ),
        migrations.AddField(
            model_name="jobrunlogentry",
            name="kind2",
            field=EnumIntegerField(
                enum=LogEntryKind, default=LogEntryKind.STDOUT, verbose_name="kind"
            ),
        ),
    ]
