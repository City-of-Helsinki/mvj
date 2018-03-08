from django.db import models
from django.utils.translation import ugettext_lazy as _


class Inspection(models.Model):
    """
    In Finnish: Tarkastukset ja huomautukset
    """
    # In Finnish: Tarkastaja
    inspector = models.CharField(verbose_name=_("Inspector"), max_length=255)

    # In Finnish: Valvonta päivämäärä
    supervision_date = models.DateField(verbose_name=_("Supervision date"))

    # In Finnish: Valvottu päivämäärä
    supervised_date = models.DateField(verbose_name=_("Supervised date"))

    # In Finnish: Selite
    inspection_description = models.TextField(verbose_name=_("Inspection description"))
