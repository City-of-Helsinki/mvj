# Generated by Django 3.2.13 on 2023-05-16 08:57

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("plotsearch", "0023_plotsearchtarget_reservation_identifier"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="IntendedUse",
            new_name="AreaSearchIntendedUse",
        ),
    ]
