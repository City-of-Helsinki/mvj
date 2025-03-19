# Generated by Django 4.2.19 on 2025-03-19 07:22

from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Add new field to Rent model: periodic rent adjustment's price index's
    point figure's year. This is needed to later decide if point figure's value
    should be updated when new figures are released.

    Update terminology in backend from "index number" to "point figure", as
    described by Tilastokeskus/StatFin.
    """

    dependencies = [
        ("leasing", "0093_remove_vipunenmaplayer_filter_by_intended_use_and_more"),
    ]

    operations = [
        # Add new field to Rent model
        migrations.RemoveField(
            model_name="rent",
            name="start_price_index_point_figure",
        ),
        migrations.AddField(
            model_name="rent",
            name="start_price_index_point_figure_value",
            field=models.DecimalField(
                decimal_places=1,
                max_digits=8,
                null=True,
                verbose_name="Start price index point figure value",
            ),
        ),
        migrations.AddField(
            model_name="rent",
            name="start_price_index_point_figure_year",
            field=models.PositiveSmallIntegerField(
                null=True, verbose_name="Start price index point figure year"
            ),
        ),
        migrations.AddConstraint(
            model_name="indexpointfigureyearly",
            constraint=models.UniqueConstraint(
                fields=("index", "year"), name="unique_price_index_point_figure"
            ),
        ),
        # Update terminology
        migrations.AlterModelOptions(
            name="indexpointfigureyearly",
            options={
                "ordering": ("-index", "-year"),
                "verbose_name": "Index point figure, yearly",
                "verbose_name_plural": "Index point figures, yearly",
            },
        ),
        migrations.RemoveConstraint(
            model_name="indexpointfigureyearly",
            name="unique_price_index_number",
        ),
    ]
