from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("batchrun", "0006_remove_some_safedeletes"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="jobrunlogentry",
            options={
                "ordering": ("-run", "time", "id"),
                "verbose_name": "log entry",
                "verbose_name_plural": "log entries",
            },
        ),
    ]
