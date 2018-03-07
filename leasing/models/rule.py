from django.db import models
from django.utils.translation import ugettext_lazy as _

from .mixins import NameModel


class RuleMaker(NameModel):
    pass


class RuleType(NameModel):
    pass


class Rule(models.Model):
    """Rule

    Name in Finnish: Päätös

    Attributes:
        rule_maker (ForeignKey):
            Name in Finnish: Päättäjä
        rule_date (DateField):
            Name in Finnish: Päätöspäivämäärä
        rule_clause (CharField):
            Name in Finnish: Pykälä
        rule_type (ForeignKey):
            Name in Finnish: Päätöksen tyyppi
        rule_description (TextField):
            Name in Finnish: Selite
    """
    rule_maker = models.ForeignKey(
        RuleMaker,
        verbose_name=_("Rule maker"),
        on_delete=models.PROTECT,
    )

    rule_date = models.DateField(
        verbose_name=_("Rule date"),
    )

    rule_clause = models.CharField(
        verbose_name=_("Rule clause"),
        max_length=255,
    )

    rule_type = models.ForeignKey(
        RuleType,
        verbose_name=_("Rule type"),
        on_delete=models.PROTECT,
    )

    rule_description = models.TextField(
        verbose_name=_("Rule description"),
    )
