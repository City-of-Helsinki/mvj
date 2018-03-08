"""These are all the models used in the construction worthiness page (Rakentamiskelpoisuus in Finnish)."""
from django.db import models
from django.utils.translation import ugettext_lazy as _

from .mixins import NameModel


class ResearchState(NameModel):
    pass


class ResearchStateMixin(models.Model):
    # In Finnish: Selvitysaste
    research_state = models.ForeignKey(ResearchState, verbose_name=_("Research state"), on_delete=models.PROTECT)

    class Meta:
        abstract = True


class Decision(models.Model):
    """All the preconstruction models use this class to keep track of decisions.

    In Finnish: Päätös
    """
    # In Finnish: Selitys
    comment = models.CharField(verbose_name=_("Comment"), max_length=255)
    # In Finnish: AHJO diaarinumero
    AHJO_number = models.CharField(verbose_name=_("AHJO number"), max_length=255)


class DecisionMixin(models.Model):
    decision = models.ForeignKey(Decision, verbose_name=_("Decision"), related_name="+", on_delete=models.CASCADE)

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
    In Finnish: Pilaantunut maa-alue (PIMA)
    """
    # In Finnish: ProjectWise kohdenumero
    projectwise_number = models.CharField(verbose_name=_("Rule clause"), max_length=255)

    # In Finnish: Matti raportti
    matti_report = models.CharField(verbose_name=_("Matti report"), max_length=255)

    # In Finnish: Vuokraehdot
    rent_condition = models.ForeignKey(RentCondition, verbose_name=_("Rent conditions"), on_delete=models.CASCADE,
                                       related_name="+")

    # In Finnish: Päivämäärä
    rent_condition_date = models.DateField(verbose_name=_("Rent condition date"))

    # In Finnish: PIMA valmistelija
    contamination_author = models.CharField(verbose_name=_("Contamination author"), max_length=255)


class ConstructionInvestigationReport(NameModel):
    pass


class ConstructionInvestigation(DecisionMixin):
    """
    In Finnish: Rakennettavuusselvitys
    """
    # In Finnish: Geotekninen palvelun tiedosto
    geotechnical_number = models.CharField(verbose_name=_("Geotechnical number"), max_length=255)

    # In Finnish: Selvitys
    report = models.ForeignKey(ConstructionInvestigationReport, verbose_name=("Report"), on_delete=models.CASCADE,
                               related_name="+")

    # In Finnish: Allekirjoituspäivämäärä
    signing_date = models.DateField(verbose_name=_("Signing date"))

    # In Finnish: Allekirjoittaja
    report_author = models.CharField(verbose_name=_("Report author"), max_length=255)


class Other(DecisionMixin):
    pass
