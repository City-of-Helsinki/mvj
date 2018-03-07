"""
These are all the models used in the construction worthiness page (Rakentamiskelpoisuus in Finnish).
"""
from django.db import models
from django.utils.translation import ugettext_lazy as _

from .mixins import NameModel


class ResearchState(NameModel):
    pass


class ResearchStateMixin(models.Model):
    research_state = models.ForeignKey(
        ResearchState,
        verbose_name=_("Research state"),
        on_delete=models.PROTECT,
    )

    class Meta:
        abstract = True


class Decision(models.Model):
    """
    All the preconstruction models use this class to keep track of decisions.

    Attributes
        AHJO_number ():
            Name in Finnish: AHJO diaarinumero
    """
    AHJO_number = models.CharField(
        verbose_name=_("AHJO number"),
        max_length=255,
    )


class DecisionMixin(models.Model):
    """
    Attributes:
        decision (ForeignKey):
            Name in Finnish: Selvitysaste
    """
    decision = models.ForeignKey(
        Decision,
        verbose_name=_("Decision"),
        related_name="+",
        on_delete=models.CASCADE,
    )

    class Meta:
        abstract = True


class Preconstuction(DecisionMixin):
    pass


class Demolition(DecisionMixin):
    pass


class RentCondition(NameModel):
    pass


class Contamination(DecisionMixin):
    """
    Attributes:
        projectwise_number (CharField):
            Name in Finnish: ProjectWise kohdenumero
        matti_report (CharField):
            Name in Finnish: Matti raportti
        rent_condition (ForeignKey)
            Name in Finnish: Vuokraehdot
        rent_condition_date (CharField):
            Name in Finnish: Päivämäärä
        contamination_author (CharField):
            Name in Finnish: PIMA valmistelija
    """
    projectwise_number = models.CharField(
        verbose_name=_("Rule clause"),
        max_length=255,
    )

    matti_report = models.CharField(
        verbose_name=_("Matti report"),
        max_length=255,
    )

    rent_condition = models.ForeignKey(
        RentCondition,
        verbose_name=_("Rent conditions"),
        on_delete=models.CASCADE,
        related_name="+",
    )

    rent_condition_date = models.DateField(
        verbose_name=_("Rent condition date"),
    )

    contamination_author = models.CharField(
        verbose_name=_("Contamination author"),
        max_length=255,
    )


class ConstructionInvestigationReport(NameModel):
    pass


class ConstructionInvestigation(DecisionMixin):
    """
    Attributes:
        geotechnical_number (CharField):
            Name in Finnish: Geotekninen palvelun tiedosto
        report (ForeignKey):
            Name in Finnish: Selvitys
        signing_date (DateField):
            Name in Finnish: Allekirjoituspäivämäärä
        report_author (CharField):
            Name in Finnish: Allekirjoittaja
    """
    geotechnical_number = models.CharField(
        verbose_name=_("Geotechnical number"),
        max_length=255,
    )

    report = models.ForeignKey(
        ConstructionInvestigationReport,
        verbose_name=("Report"),
        on_delete=models.CASCADE,
        related_name="+",
    )

    signing_date = models.DateField(
        verbose_name=_("Signing date"),
    )

    report_author = models.CharField(
        verbose_name=_("Report author"),
        max_length=255,
    )


class Other(DecisionMixin):
    pass
