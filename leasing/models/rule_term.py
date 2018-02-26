from django.db import models
from django.utils.translation import ugettext_lazy as _

from .rule import Rule


class TermPurpose(models.Model):
    pass


class RuleTerm(models.Model):
    """Rule term

    Name in Finnish: Ehto

    Attributes:
        rule (ForeignKey):
            Name in Finnish: Päätös
        term_purpose (ForeignKey):
            Name in Finnish: Käyttötarkoitusehto
        supervision_date (DateField):
            Name in Finnish: Valvonta päivämäärä
        supervised_date (DateField):
            Name in Finnish: Valvottu päivämäärä
        term_description (TextField):
            Name in Finnish: Selite
    """
    rule = models.ForeignKey(
        Rule,
        verbose_name=_("Rule"),
        on_delete=models.CASCADE,
        related_name="terms",
    )

    term_purpose = models.ForeignKey(
        TermPurpose,
        verbose_name=_("Term purpose"),
        on_delete=models.CASCADE,
        related_name="+",
    )

    supervision_date = models.DateField(
        verbose_name=_("Supervision date"),
    )

    supervised_date = models.DateField(
        verbose_name=_("Supervised date"),
    )

    term_description = models.TextField(
        verbose_name=_("Term description"),
    )
