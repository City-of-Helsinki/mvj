# Generated by Django 3.2.13 on 2022-08-17 07:03

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("forms", "0017_add_entrysection_model_add_metadata"),
        ("plotsearch", "0015_informationcheck"),
    ]

    operations = [
        migrations.AlterField(
            model_name="informationcheck",
            name="entry_section",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="forms.entrysection"
            ),
        ),
    ]
