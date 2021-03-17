from django.db import models
from django.utils.translation import pgettext_lazy
from django.utils.translation import ugettext_lazy as _
from enumfields import EnumField

from leasing.enums import DetailedPlanClass

from .mixins import TimeStampedSafeDeleteModel


class DetailedPlan(TimeStampedSafeDeleteModel):
    """
    In Finnish: Asemakaava
    """

    # In Finnish: Kaavatunnus
    identifier = models.CharField(verbose_name=_("Identifier"), max_length=45)

    # In Finnish: Hyväksyjä
    acceptor = models.CharField(verbose_name=_("Accepter"), blank=True, max_length=15)

    # In Finnish: Luokka
    detailed_plan_class = EnumField(
        DetailedPlanClass, verbose_name=_("Class"), null=True, blank=True, max_length=30
    )

    # In Finnish: Diaarinumero
    diary_number = models.CharField(
        verbose_name=_("Diary number"), blank=True, max_length=45
    )

    # In Finnish: Kaavavaihe
    plan_stage = models.CharField(
        verbose_name=_("Plan stage"), blank=True, max_length=255
    )

    # In Finnish: Lainvoimaisuus päivämäärä
    lawfulness_date = models.DateField(
        verbose_name=_("Lawfulness date"), null=True, blank=True, max_length=45
    )

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Detailed plan")
        verbose_name_plural = pgettext_lazy("Model name", "Detailed plans")

    def __str__(self):
        return self.identifier
