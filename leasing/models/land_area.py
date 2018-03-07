from auditlog.registry import auditlog
from django.db import models
from django.utils.translation import ugettext_lazy as _
from enumfields import EnumField
from safedelete.models import SafeDeleteModel

from leasing.enums import LeaseAreaType, LocationType, PlotType
from leasing.models.lease import Lease

from .mixins import NameModel, TimeStampedModel


class Land(TimeStampedModel):
    """Land is an abstract class with common fields for leased land,
    real properties, unseparated parcels, and plan units.

    In Finnish: Maa-alue
    """
    # In Finnish: Tunnus
    identifier = models.CharField(verbose_name=_("Identifier"), max_length=255)

    # In Finnish: Kokonaisala / Pinta-ala
    area = models.PositiveIntegerField(verbose_name=_("Area in square meters"))

    # In Finnish: Leikkausala
    section_area = models.PositiveIntegerField(verbose_name=_("Section area"))

    # In Finnish: Osoite
    address = models.CharField(verbose_name=_("Address"), max_length=255)

    # In Finnish: Postinumero
    postal_code = models.CharField(verbose_name=_("Postal code"), max_length=255)

    # In Finnish: Kaupunki
    city = models.CharField(verbose_name=_("City"), max_length=255)

    class Meta:
        abstract = True


class LeaseArea(Land, SafeDeleteModel):
    """
    In Finnish: Vuokra-alue
    """
    lease = models.ForeignKey(Lease, on_delete=models.PROTECT)
    type = EnumField(LeaseAreaType, verbose_name=_("Type"), max_length=30)
    # In Finnish: Sijainti (maanpäällinen, maanalainen)
    location = EnumField(LocationType, verbose_name=_("Location"))


class Plot(Land):
    """Information about a piece of land regarding a lease area

    In Finnish: Tontti, but also possibly Määräala or Kiinteistö
                depending on the context
    """
    type = EnumField(PlotType, verbose_name=_("Type"), max_length=30)
    # In Finnish: Rekisteröintipäivä
    registration_date = models.DateField(verbose_name=_("Registration date"), null=True, blank=True)
    lease_area = models.ForeignKey(LeaseArea, related_name='plots', on_delete=models.CASCADE)
    # In Finnish: Sopimushetkellä
    in_contract = models.BooleanField(verbose_name=_("At time of contract"), default=False)


class PlanUnitType(NameModel):
    """
    In Finnish: Kaavayksikön laji
    """


class PlanUnitState(NameModel):
    """
    In Finnish: Kaavayksikön olotila
    """


class PlanUnit(Land):
    """Plan plots are like the atoms of city plans.

    In Finnish: Kaavayksikkö

    Plan plots are the plan specialization of land areas. While one
    could say that they come before the parcel specializations of land
    areas, they may be planned according to preexisting land areas.
    Plan plots differ from parcels in that they cannot be physically
    owned. Plan plots can be divided (tonttijako).
    """
    type = EnumField(PlotType, verbose_name=_("Type"), max_length=30)
    lease_area = models.ForeignKey(LeaseArea, related_name='plan_units', on_delete=models.CASCADE)
    # In Finnish: Sopimushetkellä
    in_contract = models.BooleanField(verbose_name=_("At time of contract"), default=False)

    # In Finnish: Tonttijaon tunnus
    plot_division_identifier = models.CharField(verbose_name=_("Plot division identifier"), max_length=255)

    # In Finnish: Tonttijaon hyväksymispvm
    plot_division_date_of_approval = models.DateField(verbose_name=_("Plot division date of approval"))

    # In Finnish: Asemakaava
    detailed_plan_identifier = models.CharField(verbose_name=_("Detailed plan identifier"), max_length=255)

    # In Finnish: Asemakaavan vahvistumispvm
    detailed_plan_date_of_approval = models.DateField(verbose_name=_("Detailed plan date of approval"))

    # In Finnish: Kaavayksikön laji
    plan_unit_type = models.ForeignKey(PlanUnitType, verbose_name=_("Plan unit type"), on_delete=models.PROTECT)

    # In Finnish: Kaavayksikön olotila
    plan_unit_state = models.ForeignKey(PlanUnitState, verbose_name=_("Plan unit state"), on_delete=models.PROTECT)


auditlog.register(LeaseArea)
auditlog.register(Plot)
auditlog.register(PlanUnit)
