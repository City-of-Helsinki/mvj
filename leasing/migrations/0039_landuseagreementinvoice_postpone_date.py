from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("leasing", "0038_add_invoiceset_landuseagreement"),
    ]

    operations = [
        migrations.AddField(
            model_name="landuseagreementinvoice",
            name="postpone_date",
            field=models.DateField(blank=True, null=True, verbose_name="Postpone date"),
        ),
    ]
