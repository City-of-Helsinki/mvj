# Generated by Django 4.2.14 on 2024-11-20 12:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("leasing", "0080_alter_contact_options"),
    ]

    operations = [
        migrations.AddField(
            model_name="serviceunit",
            name="use_rent_override_receivable_type",
            field=models.BooleanField(
                default=False,
                help_text="Use the override receivable type from rent in automatic invoices, if it is present. When creating a rent, some service units (such as AKV and KuVa) want to select a receivable type to be used in future automatic invoices. This helps avoid some technical difficulties in invoice XML generation. Generation logic would otherwise be unaware of the desired receivable type, if it is different from the service unit's default receivable type, or the leasetype's receivable type.",
                verbose_name="Use the override receivable type from rent in automatic invoices?",
            ),
        ),
    ]
