from django.db import models
from django.utils.translation import ugettext_lazy as _


class Inspection(models.Model):
    """Inspection

    Name in Finnish: Tarkastukset ja huomautukset

    Attributes:
        inspector (CharField):
            Name in Finnish: Tarkastaja
        supervision_date (DateField):
            Name in Finnish: Valvonta päivämäärä
        supervised_date (DateField):
            Name in Finnish: Valvottu päivämäärä
        inspection_description (TextField):
            Name in Finnish: Selite
    """

    inspector = models.CharField(
        verbose_name=_("Inspector"),
        max_length=255,
    )

    supervision_date = models.DateField(
        verbose_name=_("Supervision date"),
    )

    supervised_date = models.DateField(
        verbose_name=_("Supervised date"),
    )

    inspection_description = models.TextField(
        verbose_name=_("Inspection description"),
    )
