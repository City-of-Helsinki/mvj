import re

from django.core.management.base import BaseCommand

from leasing.enums import AreaType, PlotType
from leasing.models import Area, Lease
from leasing.models.land_area import PlanUnit, PlanUnitIntendedUse, PlanUnitState, PlanUnitType, Plot, PlotDivisionState


def normalize_identifier(identifier):
    identifier = identifier.strip()
    match = re.match(r'(\d+)-(\d+)-(\d+)(?:VE|L|P)?-(\d+)-P?(\d+)', identifier)

    if match:
        return '{:03d}{:03d}{:04d}{:04d}{:03d}'.format(*[int(i) for i in match.groups()])

    match = re.match(r'(\d+)-(\d+)-(\d+)-(\d+)', identifier)
    if match:
        return '{:03d}{:03d}{:04d}{:04d}000'.format(*[int(i) for i in match.groups()])

    return identifier


def denormalize_identifier(identifier):
    if len(identifier) == 14:
        return '{}-{}-{}-{}'.format(
            int(identifier[0:3]), int(identifier[3:6]), int(identifier[6:10]), int(identifier[10:]))

    return identifier


class Command(BaseCommand):
    help = 'Attach areas'

    def handle(self, *args, **options):
        leases = Lease.objects.all()

        for lease in leases:
            self.stdout.write('Lease #{} {}:'.format(lease.id, lease.identifier))

            lease_areas = {normalize_identifier(la.identifier): la for la in lease.lease_areas.all()}
            areas = Area.objects.filter(type=AreaType.LEASE_AREA, identifier=str(lease.identifier))

            for area in areas:
                area_identifier = normalize_identifier(area.metadata['property_identifier'])
                self.stdout.write(' {} -> {}'.format(area.metadata['property_identifier'], area_identifier))
                if area_identifier not in lease_areas.keys():
                    self.stdout.write('Lease area NOT FOUND!')
                    continue

                lease_areas[area_identifier].geometry = area.geometry
                lease_areas[area_identifier].save()
                self.stdout.write(' Lease area FOUND. SAVED.')

                other_areas = Area.objects.filter(geometry__intersects=area.geometry).exclude(
                    type__in=[AreaType.LEASE_AREA, AreaType.PLOT_DIVISION])

                for other_area in other_areas:
                    self.stdout.write('  #{} {} {}'.format(other_area.id, other_area.identifier, other_area.type))

                    if other_area.type == AreaType.REAL_PROPERTY or other_area.type == AreaType.UNSEPARATED_PARCEL:
                        intersection = other_area.geometry & lease_areas[area_identifier].geometry
                        intersection.transform(3879)

                        match_data = {
                            'lease_area': lease_areas[area_identifier],
                            'type': PlotType[other_area.type.value.upper()],
                            'identifier': denormalize_identifier(other_area.identifier),
                        }
                        rest_data = {
                            'area': float(other_area.metadata.get('area')),
                            'section_area': intersection.area,
                            'registration_date': other_area.metadata.get('registration_date'),
                            'repeal_date': other_area.metadata.get('repeal_date'),
                            'geometry': other_area.geometry,
                        }
                        (plot, plot_created) = Plot.objects.update_or_create(defaults=rest_data, **match_data)
                        self.stdout.write('   Plot #{} ({}) saved.'.format(plot.id, plot.type))
                    elif other_area.type == AreaType.PLAN_UNIT:
                        # Find the plot division that intersects the most
                        plot_area = Area.objects.filter(
                            geometry__intersects=other_area.geometry, type=AreaType.PLOT_DIVISION).extra(
                                select={
                                    'interarea':
                                        'ST_Area(ST_Transform(ST_Intersection(geometry, \'{}\'), 3879))'.format(
                                            other_area.geometry)}).order_by('-interarea').first()

                        if plot_area and plot_area.interarea > 0:
                            intersection = other_area.geometry & lease_areas[area_identifier].geometry
                            intersection.transform(3879)

                            (plot_division_state, created) = PlotDivisionState.objects.get_or_create(
                                name=plot_area.metadata.get('state_name'))

                            try:
                                detailed_plan_area = Area.objects.filter(
                                    type=AreaType.DETAILED_PLAN,
                                    identifier=other_area.metadata.get('detailed_plan_identifier')).first()
                                detailed_plan_identifier = detailed_plan_area.identifier
                                detailed_plan_latest_processing_date = None
                            except Area.DoesNotExist:
                                detailed_plan_identifier = None
                                detailed_plan_latest_processing_date = None

                            (plan_unit_type, created) = PlanUnitType.objects.get_or_create(
                                name=other_area.metadata.get('type_name'))
                            (plan_unit_state, created) = PlanUnitState.objects.get_or_create(
                                name=other_area.metadata.get('state_name'))
                            (plan_unit_intended_use, created) = PlanUnitIntendedUse.objects.get_or_create(
                                name=other_area.metadata.get('intended_use_name'))

                            match_data = {
                                'lease_area': lease_areas[area_identifier],
                                'identifier': denormalize_identifier(other_area.identifier),
                            }
                            rest_data = {
                                'area': float(other_area.metadata.get('area')),
                                'section_area': intersection.area,
                                'geometry': other_area.geometry,
                                'plot_division_identifier': plot_area.identifier,
                                'plot_division_date_of_approval': plot_area.metadata.get('date_of_approval'),
                                'plot_division_state': plot_division_state,
                                'detailed_plan_identifier': detailed_plan_identifier,
                                'detailed_plan_latest_processing_date': detailed_plan_latest_processing_date,
                                'plan_unit_type': plan_unit_type,
                                'plan_unit_state': plan_unit_state,
                                'plan_unit_intended_use': plan_unit_intended_use,
                            }

                            (plan_unit, plan_unit_created) = PlanUnit.objects.update_or_create(
                                defaults=rest_data, **match_data)

                            self.stdout.write('   PlanUnit #{} saved.'.format(plan_unit.id))

            self.stdout.write('')
