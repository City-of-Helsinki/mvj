import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("leasing", "0037_landuseagreementinvoice_interest_invoice_for"),
    ]

    operations = [
        migrations.CreateModel(
            name="LandUseAgreementInvoiceSet",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "land_use_agreement",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="invoicesets",
                        to="leasing.LandUseAgreement",
                        verbose_name="Land use agreement",
                    ),
                ),
            ],
            options={
                "verbose_name": "Invoice set",
                "verbose_name_plural": "Invoice set",
            },
        ),
        migrations.AddField(
            model_name="landuseagreementinvoice",
            name="invoiceset",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="invoices",
                to="leasing.LandUseAgreementInvoiceSet",
                verbose_name="Invoice set",
            ),
        ),
    ]
