from django.db import models
from django.utils.translation import ugettext_lazy as _

from .mixins import NameModel


class DecisionMaker(NameModel):
    pass


class DecisionType(NameModel):
    pass


class Decision(models.Model):
    """
    In Finnish: Päätös
    """
    lease = models.ForeignKey('leasing.Lease', verbose_name=_("Lease"), related_name='decisions',
                              on_delete=models.PROTECT)

    # In Finnish: Päättäjä
    decision_maker = models.ForeignKey(DecisionMaker, verbose_name=_("Decision maker"), on_delete=models.PROTECT)

    # In Finnish: Päätöspäivämäärä
    decision_date = models.DateField(verbose_name=_("Decision date"))

    # In Finnish: Pykälä
    section = models.CharField(verbose_name=_("Section"), max_length=255)

    # In Finnish: Päätöksen tyyppi
    type = models.ForeignKey(DecisionType, verbose_name=_("Type"), on_delete=models.PROTECT)

    # In Finnish: Selite
    description = models.TextField(verbose_name=_("Description"))


class PurposeCondition(NameModel):
    pass


class Condition(models.Model):
    """
    In Finnish: Ehto
    """
    # In Finnish: Päätös
    decision = models.ForeignKey(Decision, verbose_name=_("Decision"), related_name="conditions",
                                 on_delete=models.CASCADE)

    # In Finnish: Käyttötarkoitusehto
    purpose = models.ForeignKey(PurposeCondition, verbose_name=_("PurposeCondition"), related_name="+",
                                on_delete=models.CASCADE)

    # In Finnish: Valvontapäivämäärä
    supervision_date = models.DateField(verbose_name=_("Supervision date"))

    # In Finnish: Valvottu päivämäärä
    supervised_date = models.DateField(verbose_name=_("Supervised date"))

    # In Finnish: Selite
    term_description = models.TextField(verbose_name=_("Term description"))
