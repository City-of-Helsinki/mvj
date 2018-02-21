from django.db import models
from django.utils.translation import ugettext_lazy as _

from .mixins import TimestampedModelMixin


class LandArea(TimestampedModelMixin):
    """Land area is an abstract class with common fields for plan plots and plots.

    While there is a difference between a plan plot and a plot, they share a lot of common fields, which are gathered
    under this class.

    Attributes:
        identifier (CharField): JHS 138 contains the specs for this, but we just treat it as text.
            Name in Finnish: Tunnus
        area (PositiveIntegerField): The actual area of the plot in total, independent of the rentals of it.
            Name in Finnish: Kokonaisala
        cross_section (PositiveIntegerField): The area of the plot that is used by this rental.
            The logic here might be better handled in a many-to-many table instead.
            Name in Finnish: Leikkausala
        address (CharField): The snail mail address of the land area.
            Name in Finnish: Osoite
        postal_code (CharField): The Finnish postal code.
            Name in Finnish: Postinumero
        city (CharField): The city this land area is in.
            Name in Finnish: Kaupunki
    """

    identifier = models.CharField(
        verbose_name=_("Identifier"),  # Tunnus
        max_length=255,
    )

    area = models.PositiveIntegerField(
        verbose_name=_("Area"),  # Kokonaisala
        null=True,
        blank=True,
    )

    cross_section = models.PositiveIntegerField(
        verbose_name=_("Cross section"),  # Leikkausala
        null=True,
        blank=True,
    )

    address = models.CharField(
        verbose_name=_("Address"),  # Osoite
        max_length=255,
    )

    postal_code = models.CharField(
        verbose_name=_("Postal code"),  # Postinumero
        max_length=255,
    )

    city = models.CharField(
        verbose_name=_("City"),  # Kaupunki
        max_length=255,
    )

    class Meta:
        abstract = True
