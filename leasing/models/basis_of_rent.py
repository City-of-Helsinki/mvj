from auditlog.registry import auditlog
from django.db import models
from django.utils.translation import ugettext_lazy as _
from enumfields import EnumField

from leasing.enums import RentRatePeriod
from leasing.models import Financing, IntendedUse, Management

from .mixins import NameModel, TimeStampedSafeDeleteModel


class BasisOfRentPlotType(NameModel):
    """
    In Finnish: Tonttityyppi
    """


class BasisOfRent(TimeStampedSafeDeleteModel):
    """
    In Finnish: Vuokrausperuste
    """
    # In Finnish: Tonttityyppi
    plot_type = models.ForeignKey(BasisOfRentPlotType, verbose_name=_("Plot type"), on_delete=models.PROTECT)

    # In Finnish: Alkupäivämäärä
    start_date = models.DateField(verbose_name=_("Start date"), null=True, blank=True)

    # In Finnish: Loppupäivämäärä
    end_date = models.DateField(verbose_name=_("End date"), null=True, blank=True)

    # In Finnish: Asemakaava
    detailed_plan_identifier = models.CharField(verbose_name=_("Detailed plan identifier"), null=True, blank=True,
                                                max_length=255)

    # In Finnish: Hallintamuoto
    management = models.ForeignKey(Management, verbose_name=_("Form of management"), null=True, blank=True,
                                   on_delete=models.PROTECT)

    # In Finnish: Rahoitusmuoto
    financing = models.ForeignKey(Financing, verbose_name=_("Form of financing"), null=True, blank=True,
                                  on_delete=models.PROTECT)

    # In Finnish: Vuokraoikeus päättyy
    lease_rights_end_date = models.DateField(verbose_name=_("Lease rights end date"), null=True, blank=True)

    # In Finnish: Indeksi
    index_number = models.PositiveIntegerField(verbose_name=_("Index number"))

    # In Finnish: Kommentti
    note = models.TextField(verbose_name=_("Note"), null=True, blank=True)


class RentRate(models.Model):
    """
    In Finnish: Hinta
    """
    basis_of_rent = models.ForeignKey(BasisOfRent, related_name='rent_rates', on_delete=models.CASCADE)

    # In Finnish: Pääkäyttötarkoitus
    intended_use = models.ForeignKey(IntendedUse, verbose_name=_("Intended use"), null=True, blank=True,
                                     on_delete=models.PROTECT)

    # In Finnish: Euroa
    rate = models.DecimalField(verbose_name=_("Rate in EUR"), decimal_places=2, max_digits=12)

    # In Finnish: Yksikkö
    period = EnumField(RentRatePeriod, verbose_name=_("Period"), max_length=20)


class PropertyIdentifier(NameModel):
    """
    In Finnish: Kiinteistötunnus
    """
    basis_of_rent = models.ForeignKey(BasisOfRent, related_name='property_identifiers', on_delete=models.CASCADE)


class BasisOfRentDecision(NameModel):
    """
    In Finnish: Päätös
    """
    basis_of_rent = models.ForeignKey(BasisOfRent, related_name='decisions', on_delete=models.CASCADE)


auditlog.register(BasisOfRent)
