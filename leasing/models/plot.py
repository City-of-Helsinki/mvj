from django.db import models
from django.utils.translation import ugettext_lazy as _

from .land_area import LandArea
from .mixins import ConfigurableTextChoice


class PlotExplanation(ConfigurableTextChoice):
    pass


class Plot(LandArea):
    """A piece of owned land.

    We combine what could be called property (Kiinteistö in Finnish) and parcel (Määräala in Finnish) under this class.
    They probably don't need separate classes since they only differ in size and ID.

    Name in Finnish: Tontti, but also possibly Määräala or Kiinteistö depending on the context, see above text.

    Attributes:
        explanation (ForeignKey): This is used to determine if a plot is a property or a parcel or any other user
            defined type of plot.
            Name in Finnish: Selite
        registration_date (DateField):
            Name in Finnish: Rekisteröintipäivä
    """

    explanation = models.ForeignKey(
        PlotExplanation,
        verbose_name=_("Explanation"),
        on_delete=models.PROTECT,
    )

    registration_date = models.DateField(
        verbose_name=_("Registration date"),
    )
