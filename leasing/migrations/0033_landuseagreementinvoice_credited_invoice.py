import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("leasing", "0032_landuseagreement_refactor_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="landuseagreementinvoice",
            name="credited_invoice",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="credit_invoices",
                to="leasing.LandUseAgreementInvoice",
                verbose_name="Credited invoice",
            ),
        ),
    ]
