# Generated by Django 3.2.23 on 2023-12-04 09:01

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("leasing", "0068_serviceunit_laske_fill_priority_and_info"),
    ]

    operations = [
        migrations.AddField(
            model_name="receivabletype",
            name="service_unit",
            field=models.ForeignKey(
                # All existing receivable types are for
                # "Maaomaisuuden kehittäminen ja tontit"
                default=1,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="receivable_types",
                to="leasing.serviceunit",
                verbose_name="Service unit",
            ),
            preserve_default=False,
        ),
    ]
