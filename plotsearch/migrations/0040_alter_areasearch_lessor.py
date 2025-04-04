# Generated by Django 4.2.16 on 2025-01-03 12:25

from django.db import migrations
import enumfields.fields
import plotsearch.enums


class Migration(migrations.Migration):

    dependencies = [
        ("plotsearch", "0039_replace_kuva_lessor"),
    ]

    operations = [
        migrations.AlterField(
            model_name="areasearch",
            name="lessor",
            field=enumfields.fields.EnumField(
                blank=True,
                default=None,
                enum=plotsearch.enums.AreaSearchLessor,
                max_length=30,
                null=True,
                verbose_name="Lessor",
            ),
        ),
    ]
