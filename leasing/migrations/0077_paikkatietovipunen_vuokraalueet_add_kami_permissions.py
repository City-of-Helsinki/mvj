from pathlib import Path

from django.db import migrations


def load_sql_file(name):
    file_path = Path(__file__).resolve().parent / name
    with open(file_path, encoding="utf-8") as file:
        return file.read()


class Migration(migrations.Migration):
    """
    Recreates the view public.paikkatietovipunen_vuokraalueet, creates the role
    `kami` if they didn't exist already, and grants kami the necessary
    permissions to select on the view.

    This migration doesn't alter the view itself, so we don't need to drop the
    view before applying the table recreation, but we keep the main SQL file
    otherwise intact to make it easier for future copy-pasting.

    NOTE: if you know that the role did not exist before, you must grant
    additional permissions after running this migration. See the SQL file
    comments in the kami role creation section for details.

    NOTE 2: the kami role creation SQL statements must also be included in
    every future migration that touches this view. Otherwise the Vipunen users
    cannot read the view properly if the table is dropped and recreated.
    """

    dependencies = [
        (
            "leasing",
            "0076_paikkatietovipunen_vuokraalueet_view_vuokraustunnus_and_tyypin_tunnus",
        ),
    ]

    operations = [
        migrations.RunSQL(
            sql=load_sql_file(
                "./0077_paikkatietovipunen_vuokraalueet_add_kami_permissions.sql"
            ),
            reverse_sql=load_sql_file(
                "./0076_paikkatietovipunen_vuokraalueet_view_vuokraustunnus_and_tyypin_tunnus.sql"
            ),
        ),
    ]
