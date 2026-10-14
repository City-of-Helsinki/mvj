from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("landuse", "0008_order_districts_alphabetically"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="paymentschedule",
            options={
                "permissions": [
                    ("approve_paymentschedule", "Can approve payment schedule"),
                ],
            },
        ),
        migrations.AlterModelOptions(
            name="invoice",
            options={
                "permissions": [
                    ("send_invoice_to_sap", "Can send invoice to SAP"),
                ],
            },
        ),
    ]
