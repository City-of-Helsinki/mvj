from django.db import migrations

from ..enums import LogEntryKind


def fill_kind2_int_of_stderr_entries(apps, schema_editor):
    """
    Fill the new kind2 field of stderr entries.

    The stdout entries are not touched, since that is the default value
    for the kind2 field and therefore already correct.
    """
    log_entry_model = apps.get_model("batchrun", "JobRunLogEntry")
    log_entries = log_entry_model.objects.all()
    log_entries.filter(kind="stderr").update(kind2=LogEntryKind.STDERR)


def fill_kind_text_of_stderr_entries(apps, schema_editor):
    """
    Fill the old textual kind field of stderr entries.

    The stdout entries are not touched, since that is the default value
    for the old kind field (at the point of running this, see (*) in
    0003_logentry_kind_1) and therefore already correct.
    """
    log_entry_model = apps.get_model("batchrun", "JobRunLogEntry")
    log_entries = log_entry_model.objects.all()
    log_entries.filter(kind2=LogEntryKind.STDERR).update(kind="stderr")


class Migration(migrations.Migration):
    dependencies = [
        ("batchrun", "0003_logentry_kind_1"),
    ]

    operations = [
        migrations.RunPython(
            code=fill_kind2_int_of_stderr_entries,
            reverse_code=fill_kind_text_of_stderr_entries,
        ),
    ]
