# Generated by Django 2.2.13 on 2021-09-13 08:24

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("forms", "0002_add_translations"),
        ("plotsearch", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="plotsearch",
            name="form",
            field=models.OneToOneField(
                null=True, on_delete=django.db.models.deletion.SET_NULL, to="forms.Form"
            ),
        ),
    ]
