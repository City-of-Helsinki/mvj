from django.db import models
from django.utils.translation import ugettext_lazy as _


class Inspection(models.Model):
    """
    In Finnish: Tarkastukset ja huomautukset
    """
    # In Finnish: Tarkastaja
    inspector = models.CharField(verbose_name=_("Inspector"), null=True, blank=True, max_length=255)

    # In Finnish: Valvonta päivämäärä
    supervision_date = models.DateField(verbose_name=_("Supervision date"), null=True, blank=True)

    # In Finnish: Valvottu päivämäärä
    supervised_date = models.DateField(verbose_name=_("Supervised date"), null=True, blank=True)

    # In Finnish: Selite
    description = models.TextField(verbose_name=_("Description"), null=True, blank=True)
