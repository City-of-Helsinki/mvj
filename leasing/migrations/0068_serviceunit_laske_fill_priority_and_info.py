# Generated by Django 3.2.18 on 2023-10-25 07:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("leasing", "0067_add_contract_number_sequence_to_service_unit"),
    ]

    operations = [
        migrations.AddField(
            model_name="serviceunit",
            name="laske_fill_priority_and_info",
            field=models.BooleanField(
                default=True,
                help_text="Fill Info and Priority data from a contact into OrderParty"
                " and BillingParty in SalesOrder when creating LASKE XML",
                verbose_name="Fill priority and info?",
            ),
        ),
    ]
