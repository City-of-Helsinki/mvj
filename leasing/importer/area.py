import psycopg2
from django.conf import settings
from django.contrib.gis import geos

from leasing.enums import AreaType
from leasing.models.area import Area, AreaSource

from .base import BaseImporter

METADATA_COLUMN_NAME_MAP = {
    'kiinteistotunnus': 'property_identifier',
    'vuokraustunnus': 'lease_identifier',
    'vuokratunnus': 'lease_identifier',
    'maaraalatunnus': 'unseparated_parcel_identifier',
    'pinta_ala_sopimuksessa': 'area',
    'pintaala': 'area',
    'osoite': 'address',
    'rekisterointipvm': 'registration_date',
    'kumoamispvm': 'repeal_date',
    'saantopvm': 'acquisition_date',
    'rekisterilaji_tunnus': 'type_identifier',
    'rekisterilaji_selite': 'type_name',
    'kayttotark_tunnus': 'intended_use_identifier',
    'kayttotark_selite': 'intended_use_name',
    'olotila_tunnus': 'state_identifier',
    'olotila_selite': 'state_name',
    'laatu_tunnus': 'kind_identifier',
    'laatu_selite': 'kind_name',
    'tyyppi_tunnus': 'type_identifier',
    'tyyppi_selite': 'type_name',
    'kaavayksikkotunnus': 'plan_unit_identifier',
    'kaavatunnus': 'detailed_plan_identifier',
    'tyyppi': 'type_name',
    'luokka': 'state_name',
    'kayttotarkoitus': 'intended_use_name',
    'tonttijakotunnus': 'plot_division_identifier',
    'hyvaksymispvm': 'date_of_approval',
    'voimaantulopvm': 'effective_date',
    'laji_tunnus': 'type_identifier',
    'laji_selite': 'type_name',
    'vaihe_tunnus': 'state_identifier',
    'vaihe_selite': 'state_name',
    'lainvoimaisuuspvm': 'final_date',
    'vahvistamispvm': 'ratify_date',
    'sopimusnumero': 'contract_number',
    'olotila': 'state_name',
    'kunta': 'municipality',
    'sijaintialue': 'district',
    'ryhma': 'group',
    'yksikko': 'unit',
    'mvj_yks': 'mvj_unit',
}


AREA_IMPORT_TYPES = {
    # Kaava
    'detailed_plan': {
        'source_name': 'Kaava: Kaavahakemisto',
        'source_identifier': 'kaava.kaavahakemisto_alueet',
        'area_type': AreaType.DETAILED_PLAN,
        'identifier_field_name': 'kaavatunnus',
        'metadata_columns': ['kaavatunnus', 'tyyppi', 'luokka', 'pintaala', 'hyvaksymispvm',
                             'lainvoimaisuuspvm', 'voimaantulopvm', 'vahvistamispvm'],
        'query': '''
        SELECT *, ST_AsText(ST_CollectionExtract(ST_MakeValid(ST_Transform(ST_CurveToLine(a.geom), 4326)), 3))
            AS geom_text
        FROM kaava.kaavahakemisto_alueet AS a
        WHERE kaavatunnus IS NOT NULL
        ''',
    },
    # Vuokra-alueet
    # 'lease_area': {
    #     'source_name': 'Tonttiosasto: vuokrausalue_paa',
    #     'source_identifier': 'tonttiosasto.vuokrausalue_paa',
    #     'area_type': AreaType.LEASE_AREA,
    #     'identifier_field_name': 'vuokratunnus',
    #     'metadata_columns': ['vuokratunnus', 'sopimusnumero', 'olotila', 'kunta', 'sijaintialue', 'ryhma', 'yksikko',
    #                          'mvj_yks'],
    #     'query': '''
    #     SELECT *, ST_AsText(ST_CollectionExtract(ST_MakeValid(ST_Transform(ST_CurveToLine(a.geom), 4326)), 3))
    #         AS geom_text
    #     FROM tonttiosasto.vuokrausalue_paa AS a
    #     WHERE vuokratunnus IS NOT NULL
    #     ''',
    # },
    # 'lease_area': {
    #     'source_name': 'Tonttiosasto: vuokrausalueet_julkinen',
    #     'source_identifier': 'tonttiosasto.to_vuokrausalueet_julkinen',
    #     'area_type': AreaType.LEASE_AREA,
    #     'identifier_field_name': 'vuokraustunnus',
    #     'metadata_columns': ['kiinteistotunnus', 'vuokraustunnus', 'pinta_ala_sopimuksessa', 'osoite'],
    #     'query': '''
    #     SELECT *, ST_AsText(ST_CollectionExtract(ST_MakeValid(ST_Transform(ST_CurveToLine(a.geom), 4326)), 3))
    #         AS geom_text
    #     FROM tonttiosasto.to_vuokrausalueet_julkinen AS a
    #     WHERE vuokraustunnus IS NOT NULL
    #     ''',
    # },
    # Kiinteistöt
    'real_property': {
        'source_name': 'Kiinteistö: Kiinteistöalue',
        'source_identifier': 'kiinteisto.kiinteisto_alue_alueet',
        'area_type': AreaType.REAL_PROPERTY,
        'identifier_field_name': 'kiinteistotunnus',
        'metadata_columns': [
            'kiinteistotunnus', 'pintaala', 'rekisterointipvm', 'kumoamispvm',
            'rekisterilaji_tunnus', 'rekisterilaji_selite', 'kayttotark_tunnus', 'kayttotark_selite',
            'olotila_tunnus', 'olotila_selite'
        ],
        'query': '''
        SELECT *, ST_AsText(ST_CollectionExtract(ST_MakeValid(ST_Transform(ST_CurveToLine(a.geom), 4326)), 3))
            AS geom_text
        FROM kiinteisto.kiinteisto_alue_alueet AS a
        WHERE kiinteistotunnus IS NOT NULL
        ''',
    },
    # Määräalat
    'unseparated_parcel': {
        'source_name': 'Kiinteistö: Määräala',
        'source_identifier': 'kiinteisto.maaraala_alue_alueet',
        'area_type': AreaType.UNSEPARATED_PARCEL,
        'identifier_field_name': 'maaraalatunnus',
        'metadata_columns': [
            'maaraalatunnus', 'pintaala', 'rekisterointipvm', 'saantopvm',
            'laatu_tunnus', 'laatu_selite', 'tyyppi_tunnus', 'tyyppi_selite',
            'olotila_tunnus', 'olotila_selite'
        ],
        'query': '''
        SELECT *, ST_AsText(ST_CollectionExtract(ST_MakeValid(ST_Transform(ST_CurveToLine(a.geom), 4326)), 3))
            AS geom_text
        FROM kiinteisto.maaraala_alue_alueet AS a
        WHERE maaraalatunnus IS NOT NULL
        ''',
    },
    # Kaavayksiköt
    'plan_unit': {
        'source_name': 'Kaava: Kaavayksiköt',
        'source_identifier': 'kaava.kaavayksikot_alueet',
        'area_type': AreaType.PLAN_UNIT,
        'identifier_field_name': 'kaavayksikkotunnus',
        'metadata_columns': [
            'kaavayksikkotunnus', 'kaavatunnus', 'tyyppi', 'luokka', 'kayttotarkoitus', 'pintaala',
        ],
        'query': '''
        SELECT *, ST_AsText(ST_CollectionExtract(ST_MakeValid(ST_Transform(ST_CurveToLine(a.geom), 4326)), 3))
            AS geom_text
        FROM kaava.kaavayksikot_alueet AS a
        WHERE kaavayksikkotunnus IS NOT NULL
        ''',
    },
    # Tonttijaot
    'plot_division': {
        'source_name': 'Kaava: Tonttijako',
        'source_identifier': 'kaava.tonttijako_alueet',
        'area_type': AreaType.PLOT_DIVISION,
        'identifier_field_name': 'tonttijakotunnus',
        'metadata_columns': [
            'tonttijakotunnus', 'hyvaksymispvm', 'voimaantulopvm', 'laji_tunnus', 'laji_selite', 'vaihe_tunnus',
            'vaihe_selite',
        ],
        'query': '''
        SELECT *, ST_AsText(ST_CollectionExtract(ST_MakeValid(ST_Transform(ST_CurveToLine(a.geom), 4326)), 3))
            AS geom_text
        FROM kaava.tonttijako_alueet AS a
        WHERE tonttijakotunnus IS NOT NULL
        ''',
    },
}


class AreaImporter(BaseImporter):
    type_name = 'area'

    def __init__(self, stdout=None, stderr=None):
        conn = psycopg2.connect(settings.AREA_DATABASE_DSN, cursor_factory=psycopg2.extras.NamedTupleCursor)
        self.cursor = conn.cursor()
        self.stdout = stdout
        self.stderr = stderr
        self.area_types = None

    @classmethod
    def add_arguments(cls, parser):
        parser.add_argument('--area-types', dest='area_types', type=str, required=False,
                            help='comma separated list of area types to import (default: all)')

    def read_options(self, options):
        if options['area_types']:
            self.area_types = []
            for area_type in options['area_types'].split(','):
                if area_type not in AREA_IMPORT_TYPES.keys():
                    raise RuntimeError('Area import type "{}" doesn\'t exist'.format(area_type))

                self.area_types.append(area_type)

    def execute(self):  # NOQA C901
        cursor = self.cursor

        if not self.area_types:
            self.area_types = AREA_IMPORT_TYPES.keys()

        errors = []

        for area_import_type in self.area_types:
            area_import = AREA_IMPORT_TYPES[area_import_type]

            self.stdout.write(area_import['source_name'])
            (source, source_created) = AreaSource.objects.get_or_create(identifier=area_import['source_identifier'],
                                                                        defaults={'name': area_import['source_name']})

            cursor.execute(area_import['query'])

            count = 0
            for row in cursor:
                metadata = {METADATA_COLUMN_NAME_MAP[column_name]: getattr(row, column_name) for column_name in
                            area_import['metadata_columns']}
                match_data = {
                    'type': area_import['area_type'],
                    'identifier': getattr(row, area_import['identifier_field_name']),
                    'external_id': row.id,
                    'source': source,
                }

                try:
                    geom = geos.GEOSGeometry(row.geom_text)
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
