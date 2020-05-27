# Generated by Django 2.2.6 on 2020-03-11 06:33

from django.db import migrations
import enumfields.fields
import leasing.enums


class Migration(migrations.Migration):

    dependencies = [("leasing", "0003_auto_20200213_1558")]

    operations = [
        migrations.AlterField(
            model_name="leasebasisofrent",
            name="area_unit",
            field=enumfields.fields.EnumField(
                default="m2",
                enum=leasing.enums.AreaUnit,
                max_length=20,
                verbose_name="Area unit",
            ),
            preserve_default=False,
        )
    ]
