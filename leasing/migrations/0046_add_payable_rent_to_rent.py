from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("leasing", "0045_move_plotsearch_to_plotsearch_app"),
    ]

    operations = [
        migrations.AddField(
            model_name="rent",
            name="payable_rent_amount",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=10,
                null=True,
                verbose_name="Payable rent amount",
            ),
        ),
        migrations.AddField(
            model_name="rent",
            name="payable_rent_end_date",
            field=models.DateField(
                blank=True, null=True, verbose_name="Payable rent end date"
            ),
        ),
        migrations.AddField(
            model_name="rent",
            name="payable_rent_start_date",
            field=models.DateField(
                blank=True, null=True, verbose_name="Payable rent start date"
            ),
        ),
    ]
