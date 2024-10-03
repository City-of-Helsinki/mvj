from pathlib import Path

from django.db import migrations

# The necessary DROP VIEW added to avoid editing the reverse sql file
DROP_VIEW_SQL_PREFIX = "DROP VIEW public.paikkatietovipunen_vuokraalueet;"


def load_sql_file(name):
    file_path = Path(__file__).resolve().parent / name
    with open(file_path, encoding="utf-8") as file:
        return file.read()


class Migration(migrations.Migration):
    dependencies = [
        ("leasing", "0075_olddwellingsinhousingcompaniespriceindex_and_more"),
    ]

    operations = [
        migrations.RunSQL(
            sql=DROP_VIEW_SQL_PREFIX
            + load_sql_file(
                "./0076_paikkatietovipunen_vuokraalueet_view_vuokraustunnus_and_tyypin_tunnus.sql"
            ),
            reverse_sql=DROP_VIEW_SQL_PREFIX
            + load_sql_file(
                "./0060_fix_paikkatietovipunen_vuokraalueet_remove_intended_use_requirement.sql"
            ),
        ),
    ]
