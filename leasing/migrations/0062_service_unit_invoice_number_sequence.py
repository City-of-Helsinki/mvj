# Generated by Django 3.2.9 on 2021-12-14 16:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("leasing", "0061_make_service_unit_required"),
    ]

    operations = [
        migrations.AddField(
            model_name="serviceunit",
            name="first_invoice_number",
            field=models.IntegerField(
                blank=True, null=True, verbose_name="First invoice number"
            ),
        ),
        migrations.AddField(
            model_name="serviceunit",
            name="invoice_number_sequence_name",
            field=models.CharField(
                blank=True,
                max_length=255,
                null=True,
                verbose_name="Invoice number sequence name",
            ),
        ),
    ]
