# Generated by Django 4.2.11 on 2024-04-09 06:58

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("forms", "0024_forms_fieldtype_to_forms_field_type_20240221_1038"),
    ]

    operations = [
        migrations.AlterField(
            model_name="answeropeningrecord",
            name="openers",
            field=models.ManyToManyField(related_name="+", to=settings.AUTH_USER_MODEL),
        ),
    ]
