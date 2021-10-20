from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("credit_integration", "0003_add_permission_for_decision_inquiry"),
    ]

    operations = [
        migrations.AlterField(
            model_name="creditdecision",
            name="operation_start_date",
            field=models.DateField(
                blank=True, null=True, verbose_name="Date of commencement of operations"
            ),
        ),
    ]
