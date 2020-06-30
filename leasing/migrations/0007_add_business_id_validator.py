# Generated by Django 2.2.12 on 2020-06-30 10:43

import re

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("leasing", "0006_increase_max_length_of_areatype_enumfield"),
    ]

    operations = [
        migrations.AlterField(
            model_name="contact",
            name="business_id",
            field=models.CharField(
                blank=True,
                max_length=255,
                null=True,
                validators=[
                    django.core.validators.RegexValidator(
                        re.compile("^.{9}$"), "Enter a valid business id.", "invalid"
                    )
                ],
                verbose_name="Business ID",
            ),
        ),
        migrations.AlterField(
            model_name="leaseholdtransferparty",
            name="business_id",
            field=models.CharField(
                blank=True,
                max_length=255,
                null=True,
                validators=[
                    django.core.validators.RegexValidator(
                        re.compile("^.{9}$"), "Enter a valid business id.", "invalid"
                    )
                ],
                verbose_name="Business ID",
            ),
        ),
    ]
