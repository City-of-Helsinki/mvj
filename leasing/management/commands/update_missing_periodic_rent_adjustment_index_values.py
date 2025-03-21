from typing import Any

from django.core.management.base import BaseCommand

from leasing.models.rent import IndexPointFigureYearly, Rent


class Command(BaseCommand):
    help = (
        "Update missing tasotarkistus values fields for Rent objects that were"
        " created when the tasotarkistus values were not yet available."
    )

    def handle(self, *args: Any, **options: Any) -> None:
        rents = Rent.objects.filter(
            old_dwellings_in_housing_companies_price_index__isnull=False,
            start_price_index_point_figure_value__isnull=True,
            start_price_index_point_figure_year__isnull=True,
        )
        if not rents.exists():
            self.stdout.write(
                "No Rent objects with missing tasotarkistus values to update."
            )
            return

        updated_count = 0

        for rent in rents:
            price_index = rent.old_dwellings_in_housing_companies_price_index
            point_figure_year: int = rent.lease.start_date.year - 1

            try:
                point_figure = IndexPointFigureYearly.objects.get(
                    index=price_index, year=point_figure_year
                )
                rent.start_price_index_point_figure_value = point_figure.value
                rent.start_price_index_point_figure_year = point_figure.year
                rent.save()
                updated_count += 1
                self.stdout.write(
                    f"Updated Rent ID {rent.pk} with index value {point_figure.value} for year {point_figure.year}."
                )
            except IndexPointFigureYearly.DoesNotExist:
                self.stdout.write(
                    f"Rent ID {rent.pk}: IndexPointFigureYearly for year {point_figure_year} is not yet available."
                )

        self.stdout.write(f"Added point figure values to {updated_count} Rent objects.")
        self.stdout.write("Done.")
