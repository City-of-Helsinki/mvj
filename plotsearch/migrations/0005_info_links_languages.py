# Generated by Django 2.2.24 on 2021-10-07 12:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("plotsearch", "0004_targetinfolink"),
    ]

    operations = [
        migrations.AlterField(
            model_name="targetinfolink",
            name="language",
            field=models.CharField(
                choices=[("fi", "Finnish"), ("sv", "Swedish"), ("en", "English")],
                max_length=255,
            ),
        ),
    ]
