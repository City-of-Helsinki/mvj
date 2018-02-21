from django.db import models
from django.utils.translation import ugettext_lazy as _

from .land_area import LandArea
from .mixins import ConfigurableTextChoice


class PlanPlotUsagePurpose(ConfigurableTextChoice):
    """Name in Finnish: Käyttötarkoitus"""
    pass


class PlanPlotType(ConfigurableTextChoice):
    """Name in Finnish: Kaavayksikön laji"""
    pass


class PlanPlotState(ConfigurableTextChoice):
    """Name in Finnish: Kaavayksikön olotila"""
    pass


class PlanPlot(LandArea):
    """Plan plots are like the atoms of city plans.

    Plan plots are the plan specialization of land areas. While one could say that they come before the parcel
    specializations of land areas, they may be planned according to preexisting land areas.
    Plan plots differ from parcels in that they cannot be physically owned.
    Plan plots can be subdivided (tonttijako).
    Name in Finnish: Kaavayksikkö

    Attributes:
        usage_purpose (ForeignKey): Usage purpose for the plan plot. Roughly equivalent to the definition of parcels.
            Name in Finnish: Käyttötarkoitus
        land_subdivision_id (str): An identifier for land subdivision.
            Name in Finnish: Tonttijaon tunnus
        land_subdivision_confirmation_date (date): The date that the land subdivision was approved.
            Name in Finnish: Tonttijaon hyväksymispvm
        city_plan_id (str): ID of the city plan.
            Name in Finnish: Asemakaava
        city_plan_confirmation_date (date): The date that the city plan was approved.
            Name in Finnish: Asemakaavan vahvistumispvm
        plan_plot_type (ForeignKey): Specifies the type of plan plot that this is.
            Name in Finnish: Kaavayksikön laji
        plan_plot_state (ForeignKey): Specifies the state of this plan plot.
            Name in Finnish: Kaavayksikön olotila
    """

    usage_purpose = models.ForeignKey(
        PlanPlotUsagePurpose,
        verbose_name=_("Usage purpose"),
        on_delete=models.PROTECT,
    )

    land_subdivision_id = models.CharField(
        verbose_name=_("Land subdivision ID"),
        max_length=255,
    )

    land_subdivision_confirmation_date = models.DateField(
        verbose_name=_("Land subdivision confirmation date"),
    )

    city_plan_id = models.CharField(
        verbose_name=_("City plan ID"),
        max_length=255,
    )

    city_plan_confirmation_date = models.DateField(
        verbose_name=_("City plan confirmation date"),
    )

    plan_plot_type = models.ForeignKey(
        PlanPlotType,
        verbose_name=_("Plan plot type"),
        on_delete=models.PROTECT,
    )

    plan_plot_state = models.ForeignKey(
        PlanPlotState,
        verbose_name=_("Plan plot state"),
        on_delete=models.PROTECT,
    )
