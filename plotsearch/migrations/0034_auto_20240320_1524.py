# Generated by Django 3.2.25 on 2024-03-20 13:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("plotsearch", "0033_areasearchintendeduse_deleted"),
    ]

    operations = [
        migrations.AddField(
            model_name="areasearchintendeduse",
            name="deleted_by_cascade",
            field=models.BooleanField(default=False, editable=False),
        ),
        migrations.AddField(
            model_name="plotsearch",
            name="deleted_by_cascade",
            field=models.BooleanField(default=False, editable=False),
        ),
        migrations.AddField(
            model_name="relatedplotapplication",
            name="deleted_by_cascade",
            field=models.BooleanField(default=False, editable=False),
        ),
        migrations.AlterField(
            model_name="areasearchintendeduse",
            name="deleted",
            field=models.DateTimeField(db_index=True, editable=False, null=True),
        ),
        migrations.AlterField(
            model_name="plotsearch",
            name="deleted",
            field=models.DateTimeField(db_index=True, editable=False, null=True),
        ),
        migrations.AlterField(
            model_name="relatedplotapplication",
            name="deleted",
            field=models.DateTimeField(db_index=True, editable=False, null=True),
        ),
    ]
