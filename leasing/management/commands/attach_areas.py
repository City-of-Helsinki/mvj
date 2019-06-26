import re

from django.contrib.gis.geos import GEOSException
from django.core.management.base import BaseCommand
from django.db import InternalError

from leasing.enums import AreaType, PlotType
from leasing.models import Area, Lease
from leasing.models.land_area import PlanUnit, PlanUnitIntendedUse, PlanUnitState, PlanUnitType, Plot, PlotDivisionState

CODE_MAP = {
    'E': 9908,
    'G': 9902,
    'K': 9901,
    'L': 9906,
    'P': 9903,
    'R': 9905,
    'T': 9902,
    'U': 9904,
    'V': 9909,
    'W': 9909,
    'VE': 9909,
}


def normalize_identifier(identifier):
    identifier = identifier.strip()
    match = re.match(r'(\d+)-(\d+)-(\d+)([A-Za-z]+)?-(\d+)-P?(\d+)', identifier)

    if match:
        groups = list(match.groups())
        code = groups.pop(3)
        if code in CODE_MAP.keys():
            groups[2] = CODE_MAP[code]

        return '{:03d}{:03d}{:04d}{:04d}{:03d}'.format(*[int(i) for i in groups])

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

    def handle(self, *args, **options):  # noqa: C901 'Command.handle' is too complex TODO
        leases = Lease.objects.all()

        for lease in leases:
            self.stdout.write('Lease #{} {}:'.format(lease.id, lease.identifier))

            lease_areas = {normalize_identifier(la.identifier): la for la in lease.lease_areas.all()}
            areas = Area.objects.filter(type=AreaType.LEASE_AREA, identifier=str(lease.identifier))

            for area in areas:
                property_identifier = '{}-{}-{}-{}{}'.format(
                    area.metadata.get('municipality', '0') if area.metadata.get('municipality') else '0',
                    area.metadata.get('district', '0') if area.metadata.get('district') else '0',
                    area.metadata.get('group', '0') if area.metadata.get('group') else '0',
                    area.metadata.get('unit', '0') if area.metadata.get('unit') else '0',
                    '-{}'.format(area.metadata.get('mvj_unit', '0')) if 'mvj_unit' in area.metadata else '',
                )
                area_identifier = normalize_identifier(property_identifier)
                self.stdout.write(' {} -> {}'.format(property_identifier, area_identifier))

                if area_identifier not in lease_areas.keys():
                    self.stdout.write('Lease area NOT FOUND!')
                    continue

                lease_areas[area_identifier].geometry = area.geometry
                lease_areas[area_identifier].save()
                self.stdout.write(' Lease area FOUND. SAVED.')

                try:
                    other_areas = Area.objects.filter(geometry__intersects=area.geometry).exclude(
                        type__in=[AreaType.LEASE_AREA, AreaType.PLOT_DIVISION]).exclude(geometry__touches=area.geometry)
                except InternalError as e:
                    self.stdout.write(str(e))
                    continue

                for other_area in other_areas:
                    self.stdout.write('  #{} {} {}'.format(other_area.id, other_area.identifier, other_area.type))

                    try:
                        intersection = other_area.geometry & lease_areas[area_identifier].geometry
                        intersection.transform(3879)
                    except GEOSException as e:
                        self.stdout.write(str(e))
                        continue

                    self.stdout.write('   intersection area {} m^2'.format(intersection.area))

                    # Discard too small intersecting areas
                    if intersection.area < 1:
                        self.stdout.write('   DISCARD')
                        continue

                    if other_area.type == AreaType.REAL_PROPERTY or other_area.type == AreaType.UNSEPARATED_PARCEL:
                        match_data = {
                            'lease_area': lease_areas[area_identifier],
                            'type': PlotType[other_area.type.value.upper()],
                            'identifier': denormalize_identifier(other_area.identifier),
                            'in_contract': False,
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
                            (plot_division_state, created) = PlotDivisionState.objects.get_or_create(
                                name=plot_area.metadata.get('state_name'))

                            detailed_plan_area = Area.objects.filter(
                                type=AreaType.DETAILED_PLAN,
                                identifier=other_area.metadata.get('detailed_plan_identifier')).first()
                            if detailed_plan_area:
                                detailed_plan_identifier = detailed_plan_area.identifier
                                detailed_plan_latest_processing_date = None
                            else:
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
                                'in_contract': False,
                            }
                            rest_data = {
                                'area': float(other_area.metadata.get('area')),
                                'section_area': intersection.area,
                                'geometry': other_area.geometry,
                                'plot_division_identifier': plot_area.identifier,
                                'plot_division_date_of_approval': plot_area.metadata.get('date_of_approval'),
                                'plot_division_effective_date': plot_area.metadata.get('effective_date'),
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
