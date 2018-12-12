from auditlog.registry import auditlog
from django.db import models
from django.utils.translation import pgettext_lazy
from django.utils.translation import ugettext_lazy as _

from field_permissions.registry import field_permissions

from .mixins import NameModel, TimeStampedSafeDeleteModel


class DecisionMaker(NameModel):
    """
    In Finnish: Päättäjä
    """
    class Meta(NameModel.Meta):
        verbose_name = pgettext_lazy("Model name", "Decision maker")
        verbose_name_plural = pgettext_lazy("Model name", "Decision makers")


class DecisionType(NameModel):
    """
    In Finnish: Päätöksen tyyppi
    """
    class Meta(NameModel.Meta):
        verbose_name = pgettext_lazy("Model name", "Decision type")
        verbose_name_plural = pgettext_lazy("Model name", "Decision types")


class Decision(TimeStampedSafeDeleteModel):
    """
    In Finnish: Päätös
    """
    lease = models.ForeignKey('leasing.Lease', verbose_name=_("Lease"), related_name='decisions',
                              on_delete=models.PROTECT)

    # In Finnish: Diaarinumero
    reference_number = models.CharField(verbose_name=_("Reference number"), null=True, blank=True, max_length=255)

    # In Finnish: Päättäjä
    decision_maker = models.ForeignKey(DecisionMaker, verbose_name=_("Decision maker"), related_name="decisions",
                                       null=True, blank=True, on_delete=models.PROTECT)

    # In Finnish: Päätöspäivämäärä
    decision_date = models.DateField(verbose_name=_("Decision date"), null=True, blank=True)

    # In Finnish: Pykälä
    section = models.CharField(verbose_name=_("Section"), null=True, blank=True, max_length=255)

    # In Finnish: Päätöksen tyyppi
    type = models.ForeignKey(DecisionType, verbose_name=_("Type"), related_name="+", null=True, blank=True,
                             on_delete=models.PROTECT)

    # In Finnish: Selite
    description = models.TextField(verbose_name=_("Description"), null=True, blank=True)

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Decision")
        verbose_name_plural = pgettext_lazy("Model name", "Decisions")


class ConditionType(NameModel):
    """
    In Finnish: Ehtotyyppi
    """
    class Meta(NameModel.Meta):
        verbose_name = pgettext_lazy("Model name", "Condition type")
        verbose_name_plural = pgettext_lazy("Model name", "Condition types")


class Condition(TimeStampedSafeDeleteModel):
    """
    In Finnish: Ehto
    """
    # In Finnish: Päätös
    decision = models.ForeignKey(Decision, verbose_name=_("Decision"), related_name="conditions",
                                 on_delete=models.PROTECT)

    # In Finnish: Ehtotyyppi
    type = models.ForeignKey(ConditionType, verbose_name=_("Type"), related_name="+", null=True,
                             blank=True, on_delete=models.PROTECT)

    # In Finnish: Valvontapäivämäärä
    supervision_date = models.DateField(verbose_name=_("Supervision date"), null=True, blank=True)

    # In Finnish: Valvottu päivämäärä
    supervised_date = models.DateField(verbose_name=_("Supervised date"), null=True, blank=True)

    # In Finnish: Selite
    description = models.TextField(verbose_name=_("Description"), null=True, blank=True)

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Condition")
        verbose_name_plural = pgettext_lazy("Model name", "Conditions")


auditlog.register(Decision)
auditlog.register(Condition)

field_permissions.register(Decision, exclude_fields=['lease', 'rentadjustment', 'contract', 'contractchange',
                                                     'leasearea'])
field_permissions.register(Condition, exclude_fields=['decision'])
