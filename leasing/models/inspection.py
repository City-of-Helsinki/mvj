from django.db import models
from django.utils.translation import ugettext_lazy as _


class Inspection(models.Model):
    """Name in Finnish: Tarkastukset ja huomautukset"""

    # Name in Finnish: Tarkastaja
    inspector = models.CharField(verbose_name=_("Inspector"), max_length=255)

    # Name in Finnish: Valvonta päivämäärä
    supervision_date = models.DateField(verbose_name=_("Supervision date"))

    # Name in Finnish: Valvottu päivämäärä
    supervised_date = models.DateField(verbose_name=_("Supervised date"))

    # Name in Finnish: Selite
    inspection_description = models.TextField(verbose_name=_("Inspection description"))
