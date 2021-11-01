from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("credit_integration", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="creditdecision",
            name="reasons",
            field=models.ManyToManyField(
                blank=True,
                to="credit_integration.CreditDecisionReason",
                verbose_name="Reasons",
            ),
        ),
    ]
