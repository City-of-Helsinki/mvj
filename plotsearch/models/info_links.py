from django.conf import settings
from django.db import models
from rest_framework.exceptions import ValidationError

from leasing.models.land_area import CustomDetailedPlan


class TargetInfoLink(models.Model):
    """
    In Finnish: Lisätietolinkki
    """

    # In Finnish: Tonttihaun kohde
    plot_search_target = models.ForeignKey(
        "plotsearch.PlotSearchTarget",
        on_delete=models.CASCADE,
        related_name="info_links",
        blank=True,
        null=True,
    )

    # In Finnish: Oma muu alue
    custom_detailed_plan = models.ForeignKey(
        CustomDetailedPlan,
        on_delete=models.CASCADE,
        related_name="info_links",
        blank=True,
        null=True,
    )

    # In Finnish: Lisätietolinkki
    url = models.URLField()

    # In Finnish: Lisätietolinkkiteksti
    description = models.CharField(max_length=255)

    # In Finnish: Kieli
    language = models.CharField(max_length=255, choices=settings.LANGUAGES)

    def clean(self) -> None:
        cleaned_data = super().clean()
        if not cleaned_data.get("plot_search_target") and not cleaned_data.get(
            "custom_detailed_plan"
        ):
            raise ValidationError
