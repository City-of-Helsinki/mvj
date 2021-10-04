from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("credit_integration", "0002_reasons_can_be_empty"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="creditdecision",
            options={
                "permissions": [
                    ("send_creditdecision_inquiry", "Can send credit decision inquiry")
                ],
                "verbose_name": "Credit decision",
                "verbose_name_plural": "Credit decisions",
            },
        ),
    ]
