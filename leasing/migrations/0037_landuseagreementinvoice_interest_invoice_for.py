import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("leasing", "0036_landuseagreementcompensationsunitprice"),
    ]

    operations = [
        migrations.AddField(
            model_name="landuseagreementinvoice",
            name="interest_invoice_for",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="interest_invoices",
                to="leasing.LandUseAgreementInvoice",
                verbose_name="Interest invoice for",
            ),
        ),
    ]
