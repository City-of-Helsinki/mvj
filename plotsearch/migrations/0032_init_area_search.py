from django.db import migrations


class Migration(migrations.Migration):
    """This migration is empty on purpose.
    The functionality of this data migration was moved to a management command:
    `generate_areasearch_form`"""

    dependencies = [
        ("plotsearch", "0031_plotsearchsubtype_require_opening_record"),
    ]

    operations = []
