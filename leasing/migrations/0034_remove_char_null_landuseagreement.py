from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("leasing", "0033_landuseagreementinvoice_credited_invoice"),
    ]

    operations = [
        migrations.AlterField(
            model_name="landuseagreementinvoicepayment",
            name="filing_code",
            field=models.CharField(blank=True, max_length=35, verbose_name="Name"),
        ),
        migrations.AlterField(
            model_name="landuseagreementreceivabletype",
            name="sap_material_code",
            field=models.CharField(
                blank=True, max_length=255, verbose_name="SAP material code"
            ),
        ),
        migrations.AlterField(
            model_name="landuseagreementreceivabletype",
            name="sap_order_item_number",
            field=models.CharField(
                blank=True, max_length=255, verbose_name="SAP order item number"
            ),
        ),
    ]
