from django.db import migrations
from enumfields.fields import EnumIntegerField

from ..enums import LogEntryKind


class Migration(migrations.Migration):
    dependencies = [
        ("batchrun", "0004_logentry_kind_2"),
    ]

    operations = [
        migrations.AlterField(
            model_name="jobrunlogentry",
            name="kind2",
            field=EnumIntegerField(enum=LogEntryKind, verbose_name="kind"),
        ),
        migrations.RemoveField(model_name="jobrunlogentry", name="kind"),
        migrations.RenameField("jobrunlogentry", "kind2", new_name="kind"),
    ]
