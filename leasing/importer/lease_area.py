from django.conf import settings
from django.contrib.gis import geos
from django.db import connection as django_connection

from leasing.enums import AreaType
from leasing.importer.area import METADATA_COLUMN_NAME_MAP
from leasing.importer.utils import rows_to_dict_list
from leasing.models.area import Area, AreaSource

from .base import BaseImporter

AREA_IMPORT_TYPES = {
    # Vuokra-alueet
    'lease_area': {
        'source_name': 'Vuokraus: vuokrausalue_paa',
        'source_identifier': 'VUOKRAUS.VUOKRAUSALUE_PAA',
        'area_type': AreaType.LEASE_AREA,
        'identifier_field_name': 'VUOKRATUNNUS',
        'metadata_columns': ['vuokratunnus', 'sopimusnumero', 'olotila', 'kunta', 'sijaintialue', 'ryhma', 'yksikko',
                             'mvj_yks'],
        'query': '''
            SELECT
                ID, VUOKRATUNNUS, SOPIMUSNUMERO, OLOTILA, KUNTA, SIJAINTIALUE, RYHMA, YKSIKKO, MVJ_YKS, HUOM, PYSYVYYS,
                sdo_util.to_wktgeometry(OGC_GEOMETRY) wkt_geom
            FROM VUOKRAUS.VUOKRAUSALUE_PAA va
        ''',
    },
}


class LeaseAreaImporter(BaseImporter):
    type_name = 'lease_area'

    def __init__(self, stdout=None, stderr=None):
        import cx_Oracle

        connection = cx_Oracle.connect(
            user=settings.LEASE_AREA_DATABASE_USER,
            password=settings.LEASE_AREA_DATABASE_PASSWORD,
            dsn=settings.LEASE_AREA_DATABASE_DSN,
            encoding="UTF-8", nencoding="UTF-8")
        self.cursor = connection.cursor()
        self.stdout = stdout
        self.stderr = stderr

    @classmethod
    def add_arguments(cls, parser):
        pass

    def read_options(self, options):
        pass

    def execute(self):  # NOQA C901
        cursor = self.cursor
        django_cursor = django_connection.cursor()

        errors = []

        area_import = AREA_IMPORT_TYPES['lease_area']

        self.stdout.write(area_import['source_name'])
        (source, source_created) = AreaSource.objects.get_or_create(identifier=area_import['source_identifier'],
                                                                    defaults={'name': area_import['source_name']})

        cursor.execute(area_import['query'])

        lease_area_rows = rows_to_dict_list(cursor)

        count = 0
        for row in lease_area_rows:
            metadata = {METADATA_COLUMN_NAME_MAP[column_name]: row.get(column_name.upper()) for column_name in
                        area_import['metadata_columns']}
            match_data = {
                'type': area_import['area_type'],
                'identifier': row.get(area_import['identifier_field_name']),
                'external_id': row.get("ID"),
                'source': source,
            }

            # There is no SRID info in the data. Assume it's 3879.
            wkt_geom_with_srid = 'SRID=3879;{}'.format(row.get('WKT_GEOM').read())

            # Convert possible curves to lines in the geometry and transform the geometry to SRID 4326
            django_cursor.execute("SELECT ST_AsText(ST_Transform(ST_CurveToLine(ST_GeomFromEWKT(%s)), 4326));",
                                  [wkt_geom_with_srid])

            geom_text = django_cursor.fetchone()[0]

            try:
                geom = geos.GEOSGeometry(geom_text)
            except geos.error.GEOSException as e:
                errors.append('id #{} error: ' + str(e))

                count += 1
                self.stdout.write('E', ending='')
                if count % 100 == 0:
                    self.stdout.write(' {}'.format(count))
                    self.stdout.flush()

                # self.stdout.write(str(e))
                continue

            if geom and isinstance(geom, geos.Polygon):
                geom = geos.MultiPolygon(geom)

            if geom and not isinstance(geom, geos.MultiPolygon):
                errors.append('id #{} error: ' + ' Error! Geometry is not a Multipolygon but "{}"\n'.format(geom))

                count += 1
                self.stdout.write('E', ending='')
                if count % 100 == 0:
                    self.stdout.write(' {}'.format(count))
                    self.stdout.flush()

                # self.stdout.write(' Error! Geometry is not a Multipolygon but "{}"\n'.format(geom))
                continue

            other_data = {
                'geometry': geom,
                'metadata': metadata,
            }

            Area.objects.update_or_create(defaults=other_data, **match_data)

            count += 1
            self.stdout.write('.', ending='')
            if count % 100 == 0:
                self.stdout.write(' {}'.format(count))
                self.stdout.flush()

        self.stdout.write(' Count {}\n'.format(count))
        if errors:
            self.stdout.write(' {} errors:\n'.format(len(errors)))
            for error in errors:
                self.stdout.write(error)
