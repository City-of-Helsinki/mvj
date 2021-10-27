from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("credit_integration", "0006_creditdecisionlog"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="creditdecisionreason",
            options={
                "verbose_name": "Credit decision reason",
                "verbose_name_plural": "Credit decision reasons",
            },
        ),
    ]
