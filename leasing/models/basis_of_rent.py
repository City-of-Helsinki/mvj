from auditlog.registry import auditlog
from django.contrib.gis.db import models
from django.utils.translation import ugettext_lazy as _
from enumfields import EnumField

from leasing.enums import AreaUnit
from leasing.models.decision import DecisionMaker
from leasing.models.rent import Index

from .mixins import NameModel, TimeStampedSafeDeleteModel


class BasisOfRentPlotType(NameModel):
    """
    In Finnish: Tonttityyppi
    """


class BasisOfRentBuildPermissionType(NameModel):
    """
    In Finnish: Rakennusoikeustyyppi
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
    management = models.ForeignKey('leasing.Management', verbose_name=_("Form of management"), null=True, blank=True,
                                   on_delete=models.PROTECT)

    # In Finnish: Rahoitusmuoto
    financing = models.ForeignKey('leasing.Financing', verbose_name=_("Form of financing"), null=True, blank=True,
                                  on_delete=models.PROTECT)

    # In Finnish: Vuokraoikeus päättyy
    lease_rights_end_date = models.DateField(verbose_name=_("Lease rights end date"), null=True, blank=True)

    # In Finnish: Indeksi
    index = models.ForeignKey(Index, verbose_name=_("Index"), null=True, blank=True, on_delete=models.PROTECT)

    # In Finnish: Kommentti
    note = models.TextField(verbose_name=_("Note"), null=True, blank=True)


class BasisOfRentRate(TimeStampedSafeDeleteModel):
    """
    In Finnish: Hinta
    """
    basis_of_rent = models.ForeignKey(BasisOfRent, verbose_name=_("Basis of rent"), related_name='rent_rates',
                                      on_delete=models.CASCADE)

    # In Finnish: Rakennusoikeustyyppi
    build_permission_type = models.ForeignKey(BasisOfRentBuildPermissionType, verbose_name=_("Build permission type"),
                                              null=True, blank=True, on_delete=models.PROTECT)

    # In Finnish: Euroa
    amount = models.DecimalField(verbose_name=_("Amount"), decimal_places=2, max_digits=12)

    # In Finnish: Yksikkö
    area_unit = EnumField(AreaUnit, verbose_name=_("Area unit"), null=True, blank=True, max_length=20)


class BasisOfRentPropertyIdentifier(models.Model):
    """
    In Finnish: Kiinteistötunnus
    """
    basis_of_rent = models.ForeignKey(BasisOfRent, verbose_name=_("Basis of rent"), related_name='property_identifiers',
                                      on_delete=models.CASCADE)
    identifier = models.CharField(verbose_name=_("Identifier"), max_length=255)


class BasisOfRentDecision(models.Model):
    """
    In Finnish: Päätös
    """
    basis_of_rent = models.ForeignKey(BasisOfRent, related_name='decisions', on_delete=models.CASCADE)

    # In Finnish: Diaarinumero
    reference_number = models.CharField(verbose_name=_("Reference number"), null=True, blank=True, max_length=255)

    # In Finnish: Päättäjä
    decision_maker = models.ForeignKey(DecisionMaker, verbose_name=_("Decision maker"),
                                       related_name="basis_of_rent_decisions", null=True, blank=True,
                                       on_delete=models.PROTECT)

    # In Finnish: Päätöspäivämäärä
    decision_date = models.DateField(verbose_name=_("Decision date"), null=True, blank=True)

    # In Finnish: Pykälä
    section = models.CharField(verbose_name=_("Section"), null=True, blank=True, max_length=255)


auditlog.register(BasisOfRent)
