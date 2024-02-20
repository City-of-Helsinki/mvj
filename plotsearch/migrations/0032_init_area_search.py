import os

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

    # Attempt to detect whether running a test.
    # https://docs.pytest.org/en/latest/example/simple.html#pytest-current-test-environment-variable
    is_test = os.environ.get("PYTEST_CURRENT_TEST") is not None

    # Skip the data migration when running tests.
    if not is_test:
        operations = [migrations.RunPython(init_area_search_form, reverse_func)]
    else:
        operations = []
