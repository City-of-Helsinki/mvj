from datetime import datetime

from django.contrib.gis.geos import GEOSException
from django.core.management.base import BaseCommand
from django.db import InternalError

from leasing.enums import AreaType, PlotType
from leasing.models import Area, Lease
from leasing.models.land_area import (
    PlanUnit,
    PlanUnitIntendedUse,
    PlanUnitState,
    PlanUnitType,
    Plot,
    PlotDivisionState,
)


class Command(BaseCommand):
    help = "Attach areas"

    def handle(self, *args, **options):  # noqa: C901 TODO
        from auditlog.registry import auditlog

        # Unregister all models from auditlog when importing
        for model in list(auditlog._registry.keys()):
            auditlog.unregister(model)

        leases = Lease.objects.all()

        for lease in leases:
            self.stdout.write("Lease #{} {}:".format(lease.id, lease.identifier))

            lease_areas = {
                la.get_normalized_identifier(): la for la in lease.lease_areas.all()
            }
            self.stdout.write(
                " Existing lease areas: {}".format(", ".join(lease_areas.keys()))
            )

            areas = Area.objects.filter(
                type=AreaType.LEASE_AREA, identifier=str(lease.identifier)
            )

            if not areas:
                self.stdout.write(
                    "Lease #{} {}: No lease areas found in area table".format(
                        lease.id, lease.identifier
                    )
                )

            for area in areas:
                plot_ids_handled = []
                plan_unit_ids_handled = []

                area_identifier = area.get_normalized_identifier()

                if area_identifier not in lease_areas.keys():
                    self.stdout.write(
                        "Lease #{} {}: Area id {} not in lease areas of lease!".format(
                            lease.id, lease.identifier, area_identifier
                        )
                    )
                    continue

                lease_areas[area_identifier].geometry = area.geometry
                lease_areas[area_identifier].save()
                self.stdout.write("  Lease area FOUND. SAVED.")

                try:
                    # Get intersected areas with lease area's geometry but exclude the type of lease area and plot
                    # division and also geometries which only touches the lease area
                    intersected_areas = (
                        Area.objects.filter(geometry__intersects=area.geometry)
                        .exclude(type__in=[AreaType.LEASE_AREA, AreaType.PLOT_DIVISION])
                        .exclude(geometry__touches=area.geometry)
                    )
                except InternalError as e:
                    self.stdout.write(str(e))
                    continue

                for intersect_area in intersected_areas:
                    self.stdout.write(
                        "  #{} {} {}".format(
                            intersect_area.id,
                            intersect_area.identifier,
                            intersect_area.type,
                        )
                    )

                    # As of 21.1.2020, there are about 250 of plan unit area objects that have {'area': None, ...}
                    # in their metadata json field. I suspect this is due to accidental duplications in the source db
                    # since it seems like there is usually another object with identical metadata and identifier fields
                    # (except also having a value for the 'area' key) to be found, which we want to actually use.
                    if not intersect_area.metadata.get("area"):
                        self.stdout.write(
                            "Lease #{} {}: DISCARD area {}: no 'area' value in metadata".format(
                                lease.id, lease.identifier, intersect_area.id
                            )
                        )
                        continue

                    try:
                        # Discard too small intersect area
                        intersection = (
                            intersect_area.geometry
                            & lease_areas[area_identifier].geometry
                        )
                        intersection.transform(3879)
                        if intersection.area < 1:
                            self.stdout.write(
                                "Lease #{} {}: DISCARD area {}: intersection area too small".format(
                                    lease.id, lease.identifier, intersect_area.id
                                )
                            )
                            continue
                    except GEOSException as e:
                        self.stdout.write(str(e))
                        continue

                    if (
                        intersect_area.type == AreaType.REAL_PROPERTY
                        or intersect_area.type == AreaType.UNSEPARATED_PARCEL
                    ):
                        # If the intersect area's type is real property (kiinteistö) or unseparated parcel (määräala)
                        # then update or create the intersect area to plots
                        match_data = {
                            "lease_area": lease_areas[area_identifier],
                            "type": PlotType[intersect_area.type.value.upper()],
                            "identifier": intersect_area.get_denormalized_identifier(),
                            "is_master": True,
                        }
                        rest_data = {
                            "area": float(intersect_area.metadata.get("area")),
                            "section_area": intersection.area,
                            "registration_date": intersect_area.metadata.get(
                                "registration_date"
                            ),
                            "repeal_date": intersect_area.metadata.get("repeal_date"),
                            "geometry": intersect_area.geometry,
                            "master_timestamp": datetime.now(),
                        }
                        (plot, plot_created) = Plot.objects.get_or_create(
                            defaults=rest_data, **match_data
                        )
                        if not plot_created:
                            rest_data.pop("master_timestamp")
                            for attr, value in rest_data.items():
                                setattr(plot, attr, value)
                            plot.save()

                        plot_ids_handled.append(plot.id)

                        self.stdout.write(
                            "Lease #{} {}: Plot #{} ({}) saved".format(
                                lease.id, lease.identifier, plot.id, plot.type
                            )
                        )
                    elif intersect_area.type == AreaType.PLAN_UNIT:
                        # Find the plot division (tonttijako) that intersects the most
                        plot_division_area = (
                            Area.objects.filter(
                                geometry__intersects=intersect_area.geometry,
                                type=AreaType.PLOT_DIVISION,
                            )
                            .extra(
                                select={
                                    "interarea": "ST_Area(ST_Transform(ST_Intersection(geometry, '{}'), 3879))".format(
                                        intersect_area.geometry
                                    )
                                }
                            )
                            .order_by("-interarea")
                            .first()
                        )

                        # If the plot division area exist then create/update plan unit informations
                        if plot_division_area and plot_division_area.interarea > 0:
                            # Get or create plot division state
                            (
                                plot_division_state,
                                created,
                            ) = PlotDivisionState.objects.get_or_create(
                                name=plot_division_area.metadata.get("state_name")
                            )

                            # Get detailed plan area
                            detailed_plan_area = Area.objects.filter(
                                type=AreaType.DETAILED_PLAN,
                                identifier=intersect_area.metadata.get(
                                    "detailed_plan_identifier"
                                ),
                            ).first()

                            # The variable is unused for some reason
                            detailed_plan_latest_processing_date = None

                            # If detailed plan area exist, set the identifier
                            detailed_plan_identifier = None
                            if detailed_plan_area:
                                detailed_plan_identifier = detailed_plan_area.identifier

                            # Get or create plan unit type
                            (
                                plan_unit_type,
                                created,
                            ) = PlanUnitType.objects.get_or_create(
                                name=intersect_area.metadata.get("type_name")
                            )

                            # Get or create plan unit state
                            (
                                plan_unit_state,
                                created,
                            ) = PlanUnitState.objects.get_or_create(
                                name=intersect_area.metadata.get("state_name")
                            )

                            # If the intersect area has intended use name, get or create it to plan unit intended use
                            plan_unit_intended_use = None
                            if intersect_area.metadata.get("intended_use_name"):
                                (
                                    plan_unit_intended_use,
                                    created,
                                ) = PlanUnitIntendedUse.objects.get_or_create(
                                    name=intersect_area.metadata.get(
                                        "intended_use_name"
                                    )
                                )

                            match_data = {
                                "lease_area": lease_areas[area_identifier],
                                "identifier": intersect_area.get_denormalized_identifier(),
                                "is_master": True,
                            }
                            rest_data = {
                                "area": float(intersect_area.metadata.get("area")),
                                "section_area": intersection.area,
                                "geometry": intersect_area.geometry,
                                "plot_division_identifier": plot_division_area.identifier,
                                "plot_division_date_of_approval": plot_division_area.metadata.get(
                                    "date_of_approval"
                                ),
                                "plot_division_effective_date": plot_division_area.metadata.get(
                                    "effective_date"
                                ),
                                "plot_division_state": plot_division_state,
                                "detailed_plan_identifier": detailed_plan_identifier,
                                "detailed_plan_latest_processing_date": detailed_plan_latest_processing_date,
                                "plan_unit_type": plan_unit_type,
                                "plan_unit_state": plan_unit_state,
                                "plan_unit_intended_use": plan_unit_intended_use,
                                "plan_unit_status": plan_unit_state.to_enum(),
                                "master_timestamp": datetime.now(),
                            }

                            # Get or create plan unit
                            (
                                plan_unit,
                                plan_unit_created,
                            ) = PlanUnit.objects.get_or_create(
                                defaults=rest_data, **match_data
                            )
                            if not plan_unit_created:
                                rest_data.pop("master_timestamp")
                                for attr, value in rest_data.items():
                                    setattr(plan_unit, attr, value)
                                plan_unit.save()

                            plan_unit_ids_handled.append(plan_unit.id)

                            self.stdout.write(
                                "Lease #{} {}: PlanUnit #{} saved".format(
                                    lease.id, lease.identifier, plan_unit.id
                                )
                            )

                Plot.objects.filter(lease_area=lease_areas[area_identifier]).exclude(
                    id__in=plot_ids_handled
                ).delete()

                PlanUnit.objects.filter(
                    lease_area=lease_areas[area_identifier]
                ).exclude(id__in=plan_unit_ids_handled).delete()
