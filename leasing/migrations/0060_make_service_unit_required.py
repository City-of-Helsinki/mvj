# Generated by Django 3.2.9 on 2021-12-09 14:45

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("leasing", "0059_initialize_service_units"),
    ]

    operations = [
        migrations.AlterField(
            model_name="contact",
            name="service_unit",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="contacts",
                to="leasing.serviceunit",
                verbose_name="Service unit",
            ),
        ),
        migrations.AlterField(
            model_name="invoice",
            name="service_unit",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="invoices",
                to="leasing.serviceunit",
                verbose_name="Service unit",
            ),
        ),
        migrations.AlterField(
            model_name="lease",
            name="service_unit",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="leases",
                to="leasing.serviceunit",
                verbose_name="Service unit",
            ),
        ),
    ]
