# Generated by Django 4.2.20 on 2025-04-23 13:05

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("plotsearch", "0043_areasearchattachment_user_amr_list"),
    ]

    operations = [
        migrations.AddField(
            model_name="areasearch",
            name="settled_date",
            field=models.DateTimeField(
                blank=True, null=True, verbose_name="Time settled"
            ),
        ),
    ]
