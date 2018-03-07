from django.db import models
from django.utils.translation import ugettext_lazy as _

from .rule import Rule


class TermPurpose(models.Model):
    pass


class RuleTerm(models.Model):
    """Name in Finnish: Ehto"""

    # Name in Finnish: Päätös
    rule = models.ForeignKey(Rule, verbose_name=_("Rule"), on_delete=models.CASCADE, related_name="terms")

    # Name in Finnish: Käyttötarkoitusehto
    term_purpose = models.ForeignKey(TermPurpose, verbose_name=_("Term purpose"), on_delete=models.CASCADE,
                                     related_name="+")

    # Name in Finnish: Valvonta päivämäärä
    supervision_date = models.DateField(verbose_name=_("Supervision date"))

    # Name in Finnish: Valvottu päivämäärä
    supervised_date = models.DateField(verbose_name=_("Supervised date"))

    # Name in Finnish: Selite
    term_description = models.TextField(verbose_name=_("Term description"))
