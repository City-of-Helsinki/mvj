# Generated by Django 3.2.23 on 2024-02-21 08:38

from django.db import migrations, models


def migrate_field_types(apps, schema_editor):
    """Move data from ForeignKey type.identifier to temporary_type field."""
    Field = apps.get_model("forms", "Field")  # noqa: N806

    field_types = [
        "textbox",
        "textarea",
        "dropdown",
        "checkbox",
        "radiobutton",
        "radiobuttoninline",
        "uploadfiles",
        "fractional",
    ]

    # Use temporary field `temporary_type` to store the type identifier from FieldType
    for field in Field.objects.all():
        if field.type.identifier in field_types:
            field.temporary_type = field.type.identifier
        else:
            field.temporary_type = f"fixme_{field.type.identifier}"
        field.save()


class Migration(migrations.Migration):
    """Move data from forms.FieldType model to forms.Field.type"""

    dependencies = [
        ("forms", "0023_create_form_view"),
    ]

    operations = [
        migrations.AddField(
            model_name="field",
            name="temporary_type",
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.RunPython(
            migrate_field_types, reverse_code=migrations.RunPython.noop
        ),
        migrations.AlterField(
            model_name="field",
            name="type",
            field=models.ForeignKey(
                to="forms.FieldType",
                null=True,
                on_delete=models.CASCADE,
            ),
        ),
        migrations.RunSQL(
            sql="SELECT 1;-- Forward migration does nothing",
            reverse_sql="""
            UPDATE forms_field SET type_id = (SELECT id FROM forms_fieldtype WHERE identifier = 'textbox')
                WHERE temporary_type = 'textbox';
            UPDATE forms_field SET type_id = (SELECT id FROM forms_fieldtype WHERE identifier = 'textarea')
                WHERE temporary_type = 'textarea';
            UPDATE forms_field SET type_id = (SELECT id FROM forms_fieldtype WHERE identifier = 'dropdown')
                WHERE temporary_type = 'dropdown';
            UPDATE forms_field SET type_id = (SELECT id FROM forms_fieldtype WHERE identifier = 'checkbox')
                WHERE temporary_type = 'checkbox';
            UPDATE forms_field SET type_id = (SELECT id FROM forms_fieldtype WHERE identifier = 'radiobutton')
                WHERE temporary_type = 'radiobutton';
            UPDATE forms_field SET type_id = (SELECT id FROM forms_fieldtype WHERE identifier = 'radiobuttoninline')
                WHERE temporary_type = 'radiobuttoninline';
            UPDATE forms_field SET type_id = (SELECT id FROM forms_fieldtype WHERE identifier = 'uploadfiles')
                WHERE temporary_type = 'uploadfiles';
            UPDATE forms_field SET type_id = (SELECT id FROM forms_fieldtype WHERE identifier = 'fractional')
                WHERE temporary_type = 'fractional';
            UPDATE forms_field SET type_id = (SELECT id FROM forms_fieldtype WHERE identifier = 'textbox')
                WHERE temporary_type NOT IN ('textbox', 'textarea', 'dropdown', 'checkbox', 'radiobutton',
                'radiobuttoninline', 'uploadfiles', 'fractional');
            """,
        ),
        # RunSQL in order to avoid issues with model managers that might not exist in the code
        migrations.RunSQL(
            sql="SELECT 1;-- Forward migration does nothing",
            reverse_sql="""
            INSERT INTO forms_fieldtype (identifier, name) VALUES
            ('textbox', 'Tekstikenttä'),
            ('textarea', 'Tekstialue'),
            ('dropdown', 'Alasvetovalikko'),
            ('checkbox', 'Valintaruutu'),
            ('radiobutton', 'Radiopainike'),
            ('radiobuttoninline', 'Radiopainike linjassa'),
            ('uploadfiles', 'Lataa tiedosto'),
            ('fractional', 'Murtoluku');
            """,
        ),
        migrations.RemoveField(
            model_name="field",
            name="type",
        ),
        migrations.RenameField(
            model_name="field",
            old_name="temporary_type",
            new_name="type",
        ),
        migrations.AlterField(
            model_name="field",
            name="type",
            field=models.CharField(
                choices=[
                    ("textbox", "Tekstikenttä"),
                    ("textarea", "Tekstialue"),
                    ("dropdown", "Alasvetovalikko"),
                    ("checkbox", "Valintaruutu"),
                    ("radiobutton", "Radiopainike"),
                    ("radiobuttoninline", "Radiopainike linjassa"),
                    ("uploadfiles", "Lataa tiedosto"),
                    ("fractional", "Murtoluku"),
                ],
                max_length=255,
            ),
        ),
        migrations.DeleteModel(
            name="FieldType",
        ),
    ]
