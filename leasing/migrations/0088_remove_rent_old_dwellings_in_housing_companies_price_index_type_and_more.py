# Generated by Django 4.2.16 on 2024-12-23 08:42

from django.db import migrations
import enumfields.fields
import leasing.enums


class Migration(migrations.Migration):

    dependencies = [
        ("leasing", "0087_permissions_view_20250102_1632"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="rent",
            name="old_dwellings_in_housing_companies_price_index_type",
        ),
        migrations.AddField(
            model_name="rent",
            name="periodic_rent_adjustment_type",
            field=enumfields.fields.EnumField(
                blank=True,
                enum=leasing.enums.PeriodicRentAdjustmentType,
                max_length=20,
                null=True,
                verbose_name="Periodic Rent Adjustment Type",
            ),
        ),
    ]
