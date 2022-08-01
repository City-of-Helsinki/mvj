from django.core import management
from django.db import migrations
from forms.models import FieldType
from plotsearch.utils import initialize_area_search_form


def init_area_search_form(apps, schema_editor):
    if not FieldType.objects.exists():
        management.call_command("loaddata", "forms/fixtures/field_types.json")
    initialize_area_search_form()


def reverse_func(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("plotsearch", "0031_plotsearchsubtype_require_opening_record"),
    ]

    operations = [
        migrations.RunPython(init_area_search_form, reverse_func),
    ]