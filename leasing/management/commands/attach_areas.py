import logging
import sys
from typing import Any, Protocol, cast

from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.geos.error import GEOSException
from django.core.management.base import BaseCommand
from django.db import InternalError
from django.db.models import QuerySet
from django.utils import timezone

from leasing.enums import AreaType, PlotType
from leasing.models import Area, Lease, LeaseArea
from leasing.models.land_area import (
    PlanUnit,
    PlanUnitIntendedUse,
    PlanUnitState,
    PlanUnitType,
    Plot,
    PlotDivisionState,
)

LOG = logging.getLogger(__name__)


class PlotDivisionArea(Protocol):
    identifier: str
    metadata: dict[str, Any]
    interarea: float


class Command(BaseCommand):
    help = "Attach areas"

    def handle(self, *_args: Any, **options: Any) -> None:
        del _args
        configure_logging(options.get("verbosity", 0))
        unregister_audited_models()

        leases = Lease.objects.all()
        LOG.info("Processing %s leases.", leases.count())

        for lease in leases:
            process_lease(lease)


def configure_logging(verbosity: int) -> None:
    """Apply the command's verbosity conventions to area reconciliation logs."""
    logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)

    if verbosity == 0:
        LOG.setLevel(logging.WARNING)
    elif verbosity >= 2:
        LOG.setLevel(logging.DEBUG)


def unregister_audited_models() -> None:
    """Keep imported spatial data out of the application's audit history."""
    from auditlog.registry import auditlog

    for model in list(auditlog._registry.keys()):
        auditlog.unregister(model)


def process_lease(lease: Lease) -> None:
    """Reconcile imported spatial data for one lease."""
    LOG.debug("Lease #%s %s:", lease.pk, lease.identifier)

    lease_areas = get_lease_areas_by_identifier(lease)
    LOG.debug(" Existing lease areas: %s", ", ".join(lease_areas.keys()))

    imported_lease_areas = Area.objects.filter(
        type=AreaType.LEASE_AREA, identifier=str(lease.identifier)
    )
    if not imported_lease_areas:
        LOG.debug(
            "Lease #%s %s: No lease areas found in area table",
            lease.pk,
            lease.identifier,
        )

    for imported_lease_area in imported_lease_areas:
        process_imported_lease_area(lease, imported_lease_area, lease_areas)


def get_lease_areas_by_identifier(lease: Lease) -> dict[str, LeaseArea]:
    """Index the lease's existing areas by the land identifier used by imports."""
    return {
        lease_area.get_normalized_identifier(): lease_area
        for lease_area in LeaseArea.objects.filter(lease=lease)
    }


def process_imported_lease_area(
    lease: Lease,
    imported_lease_area: Area,
    lease_areas: dict[str, LeaseArea],
) -> None:
    """Reconcile one imported lease geometry and its derived land records."""
    area_identifier = imported_lease_area.get_normalized_identifier()
    lease_area = lease_areas.get(area_identifier)
    if lease_area is None:
        LOG.debug(
            "Lease #%s %s: Area id %s not in lease areas of lease!",
            lease.pk,
            lease.identifier,
            area_identifier,
        )
        return

    lease_area.geometry = imported_lease_area.geometry
    lease_area.save()

    try:
        intersected_areas = get_intersected_areas(imported_lease_area)
    except InternalError:
        LOG.exception("Failed to get intersected areas")
        return

    plot_ids_handled: list[int] = []
    plan_unit_ids_handled: list[int] = []
    for imported_area in intersected_areas:
        plot_id, plan_unit_id = process_intersected_area(
            lease, lease_area, imported_area
        )
        if plot_id is not None:
            plot_ids_handled.append(plot_id)
        if plan_unit_id is not None:
            plan_unit_ids_handled.append(plan_unit_id)

    delete_stale_derived_land(lease_area, plot_ids_handled, plan_unit_ids_handled)


def get_intersected_areas(imported_lease_area: Area) -> QuerySet[Area]:
    """Find imported land candidates that overlap the lease beyond its boundary."""
    return (
        Area.objects.filter(geometry__intersects=imported_lease_area.geometry)
        .exclude(type__in=[AreaType.LEASE_AREA, AreaType.PLOT_DIVISION])
        .exclude(geometry__touches=imported_lease_area.geometry)
    )


def process_intersected_area(
    lease: Lease,
    lease_area: LeaseArea,
    imported_area: Area,
) -> tuple[int | None, int | None]:
    """Reconcile one imported candidate with the lease's derived land records."""
    LOG.debug(
        "  #%s %s %s",
        imported_area.pk,
        imported_area.identifier,
        imported_area.type,
    )

    # Some source records are duplicates whose area value is missing. The
    # corresponding complete source record is the authoritative candidate.
    if not imported_area.metadata.get("area"):
        LOG.debug(
            "Lease #%s %s: DISCARD area %s: no 'area' value in metadata",
            lease.pk,
            lease.identifier,
            imported_area.pk,
        )
        return None, None

    intersection = get_significant_intersection(lease, imported_area, lease_area)
    if intersection is None:
        return None, None

    if imported_area.type in (
        AreaType.REAL_PROPERTY,
        AreaType.UNSEPARATED_PARCEL,
    ):
        return save_plot(lease, lease_area, imported_area, intersection), None

    if imported_area.type == AreaType.PLAN_UNIT:
        return None, save_plan_unit(lease, lease_area, imported_area, intersection)

    return None, None


def get_significant_intersection(
    lease: Lease, imported_area: Area, lease_area: LeaseArea
) -> GEOSGeometry | None:
    """Measure overlap in the local projection and discard spatial noise."""
    try:
        intersection = imported_area.geometry & lease_area.geometry
        intersection.transform(3879)
        if intersection.area < 1:
            LOG.debug(
                "Lease #%s %s: DISCARD area %s: intersection area too small",
                lease.pk,
                lease.identifier,
                imported_area.pk,
            )
            return None
    except GEOSException as error:
        LOG.exception("Discarding too small intersect area failed %s", error)
        return None

    return intersection


def save_plot(
    lease: Lease,
    lease_area: LeaseArea,
    imported_area: Area,
    intersection: GEOSGeometry,
) -> int:
    """Synchronize an imported property or parcel with its master lease plot."""
    match_data = {
        "lease_area": lease_area,
        "type": PlotType[imported_area.type.value.upper()],
        "identifier": imported_area.get_denormalized_identifier(),
        "is_master": True,
    }
    imported_data = {
        "area": float(imported_area.metadata.get("area")),
        "section_area": intersection.area,
        "registration_date": imported_area.metadata.get("registration_date"),
        "repeal_date": imported_area.metadata.get("repeal_date"),
        "geometry": imported_area.geometry,
        "master_timestamp": timezone.now(),
    }
    plot, plot_created = Plot.objects.get_or_create(
        defaults=imported_data, **match_data
    )
    if not plot_created:
        imported_data.pop("master_timestamp")
        for attribute, value in imported_data.items():
            setattr(plot, attribute, value)
        plot.save()

    LOG.debug(
        "Lease #%s %s: Plot #%s (%s) saved",
        lease.pk,
        lease.identifier,
        plot.pk,
        plot.type,
    )
    return plot.pk


def save_plan_unit(
    lease: Lease,
    lease_area: LeaseArea,
    imported_area: Area,
    intersection: GEOSGeometry,
) -> int | None:
    """Synchronize an imported plan unit when plot-division context is available."""
    plot_division_area = get_most_overlapping_plot_division(imported_area)
    if not plot_division_area or plot_division_area.interarea <= 0:
        return None

    plot_division_state, _ = PlotDivisionState.objects.get_or_create(
        name=plot_division_area.metadata.get("state_name")
    )
    plan_unit_type, _ = PlanUnitType.objects.get_or_create(
        name=imported_area.metadata.get("type_name")
    )
    plan_unit_state, _ = PlanUnitState.objects.get_or_create(
        name=imported_area.metadata.get("state_name")
    )

    match_data = {
        "lease_area": lease_area,
        "identifier": imported_area.get_denormalized_identifier(),
        "is_master": True,
    }
    imported_data = {
        "area": float(imported_area.metadata.get("area")),
        "section_area": intersection.area,
        "geometry": imported_area.geometry,
        "plot_division_identifier": plot_division_area.identifier,
        "plot_division_date_of_approval": plot_division_area.metadata.get(
            "date_of_approval"
        ),
        "plot_division_effective_date": plot_division_area.metadata.get(
            "effective_date"
        ),
        "plot_division_state": plot_division_state,
        "detailed_plan_identifier": get_detailed_plan_identifier(imported_area),
        "detailed_plan_latest_processing_date": None,
        "plan_unit_type": plan_unit_type,
        "plan_unit_state": plan_unit_state,
        "plan_unit_intended_use": get_plan_unit_intended_use(imported_area),
        "master_timestamp": timezone.now(),
    }

    plan_unit_status = plan_unit_state.to_enum()
    if plan_unit_status is not None:
        imported_data["plan_unit_status"] = plan_unit_status

    plan_unit, plan_unit_created = PlanUnit.objects.get_or_create(
        defaults=imported_data, **match_data
    )
    if not plan_unit_created:
        imported_data.pop("master_timestamp")
        for attribute, value in imported_data.items():
            setattr(plan_unit, attribute, value)
        plan_unit.save()

    LOG.debug(
        "Lease #%s %s: PlanUnit #%s saved",
        lease.pk,
        lease.identifier,
        plan_unit.pk,
    )
    return plan_unit.pk


def get_most_overlapping_plot_division(
    imported_area: Area,
) -> PlotDivisionArea | None:
    """Select the plot division used to enrich an imported plan unit."""
    plot_division_area = (
        Area.objects.filter(
            geometry__intersects=imported_area.geometry,
            type=AreaType.PLOT_DIVISION,
        )
        .extra(
            select={
                "interarea": "ST_Area(ST_Transform(ST_Intersection(geometry, '{}'), 3879))".format(
                    imported_area.geometry
                )
            }
        )
        .order_by("-interarea")
        .first()
    )
    return cast(PlotDivisionArea | None, plot_division_area)


def get_detailed_plan_identifier(imported_area: Area) -> str | None:
    """Resolve the plan identifier associated with an imported plan unit."""
    detailed_plan_area = Area.objects.filter(
        type=AreaType.DETAILED_PLAN,
        identifier=imported_area.metadata.get("detailed_plan_identifier"),
    ).first()
    return detailed_plan_area.identifier if detailed_plan_area else None


def get_plan_unit_intended_use(imported_area: Area) -> PlanUnitIntendedUse | None:
    """Resolve the optional intended-use classification for a plan unit."""
    intended_use_name = imported_area.metadata.get("intended_use_name")
    if not intended_use_name:
        return None

    intended_use, _ = PlanUnitIntendedUse.objects.get_or_create(name=intended_use_name)
    return intended_use


def delete_stale_derived_land(
    lease_area: LeaseArea,
    plot_ids_handled: list[int],
    plan_unit_ids_handled: list[int],
) -> None:
    """Remove derived land absent from the current import while preserving contracts."""
    delete_filters = {"lease_area": lease_area, "in_contract": False}
    Plot.objects.filter(**delete_filters).exclude(id__in=plot_ids_handled).delete()
    PlanUnit.objects.filter(**delete_filters).exclude(
        id__in=plan_unit_ids_handled
    ).delete()
