from time import perf_counter

import psycopg2
from django.conf import settings
from django.contrib.gis import geos
from django.core.exceptions import MultipleObjectsReturned

from leasing.enums import AreaType
from leasing.models.area import Area, AreaSource

from .base import BaseImporter

METADATA_COLUMN_NAME_MAP = {
    "diaarinumero": "diary_number",
    "hyvaksyja": "acceptor",
    "kaavavaihe": "plan_stage",
    "kiinteistotunnus": "property_identifier",
    "vuokraustunnus": "lease_identifier",
    "vuokratunnus": "lease_identifier",
    "maaraalatunnus": "unseparated_parcel_identifier",
    "pinta_ala_sopimuksessa": "area",
    "pintaala": "area",
    "rekisteriala": "area",
    "osoite": "address",
    "rekisterointipvm": "registration_date",
    "kumoamispvm": "repeal_date",
    "saantopvm": "acquisition_date",
    "rekisterilaji_tunnus": "type_identifier",
    "rekisterilaji_selite": "type_name",
    "kayttotark_tunnus": "intended_use_identifier",
    "kayttotark_selite": "intended_use_name",
    "olotila_tunnus": "state_identifier",
    "olotila_selite": "state_name",
    "laatu_tunnus": "kind_identifier",
    "laatu_selite": "kind_name",
    "tyyppi_tunnus": "type_identifier",
    "tyyppi_selite": "type_name",
    "kaavayksikkotunnus": "plan_unit_identifier",
    "kaavatunnus": "detailed_plan_identifier",
    "tyyppi": "type_name",
    "luokka": "state_name",
    "kayttotarkoitus": "intended_use_name",
    "tonttijakotunnus": "plot_division_identifier",
    "hyvaksymispvm": "date_of_approval",
    "voimaantulopvm": "effective_date",
    "laji_tunnus": "type_identifier",
    "laji_selite": "type_name",
    "vaihe_tunnus": "state_identifier",
    "vaihe_selite": "state_name",
    "lainvoimaisuuspvm": "final_date",
    "vahvistamispvm": "ratify_date",
    "sopimusnumero": "contract_number",
    "olotila": "state_name",
    "kunta": "municipality",
    "sijaintialue": "district",
    "ryhma": "group",
    "yksikko": "unit",
    "mvj_yks": "mvj_unit",
}


AREA_IMPORT_TYPES = {
    # Kaavat
    "detailed_plan": {
        "source_dsn_setting_name": "AREA_DATABASE_DSN",
        "source_name": "Kaava: Kaavahakemisto",
        "source_identifier": "kaava.kaavahakemisto_alueet",
        "area_type": AreaType.DETAILED_PLAN,
        "identifier_field_name": "kaavatunnus",
        "metadata_columns": [
            "kaavatunnus",
            "tyyppi",
            "luokka",
            "pintaala",
            "hyvaksymispvm",
            "lainvoimaisuuspvm",
            "voimaantulopvm",
            "vahvistamispvm",
        ],
        "query": """
        SELECT *, ST_AsText(ST_CollectionExtract(ST_MakeValid(ST_Transform(ST_CurveToLine(a.geom), 4326)), 3))
            AS geom_text
        FROM kaava.kaavahakemisto_alueet AS a
        WHERE kaavatunnus IS NOT NULL
        """,
    },
    # Vireillä ja tulevat asemakaavat
    "pre_detailed_plan": {
        "source_dsn_setting_name": "LEASE_AREA_DATABASE_DSN",
        "source_name": "Maka: Hankerajaus",
        "source_identifier": "maka.hankerajaus_alue_kaavahanke",
        "area_type": AreaType.PRE_DETAILED_PLAN,
        "identifier_field_name": "kaavatunnus",
        "metadata_columns": [
            "kaavatunnus",
            "diaarinumero",
            "kaavavaihe",
            "hyvaksyja",
        ],
        "query": """
        SELECT *, ST_AsText(ST_CollectionExtract(ST_MakeValid(ST_Transform(ST_CurveToLine(a.geom), 4326)), 3))
            AS geom_text
        FROM maka.hankerajaus_alue_kaavahanke AS a
        WHERE kaavatunnus IS NOT NULL
        """,
    },
    # Vuokra-alueet
    "lease_area": {
        "source_dsn_setting_name": "LEASE_AREA_DATABASE_DSN",
        "source_name": "Tonttiosasto: vuokrausalue_paa",
        "source_identifier": "tonttiosasto.vuokrausalue_paa",
        "area_type": AreaType.LEASE_AREA,
        "identifier_field_name": "vuokratunnus",
        "metadata_columns": [
            "vuokratunnus",
            "sopimusnumero",
            "olotila",
            "kunta",
            "sijaintialue",
            "ryhma",
            "yksikko",
            "mvj_yks",
        ],
        "query": """
        SELECT *, ST_AsText(ST_CollectionExtract(ST_MakeValid(ST_Transform(ST_CurveToLine(a.geom), 4326)), 3))
            AS geom_text
        FROM tonttiosasto.vuokrausalue_paa AS a
        WHERE vuokratunnus IS NOT NULL
        AND geom IS NOT NULL
        AND NOT UPPER(olotila) LIKE 'PÄÄTTYNYT'
        AND kunta IS NOT NULL
        AND sijaintialue IS NOT NULL
        AND ryhma IS NOT NULL
        AND yksikko IS NOT NULL
        """,
    },
    # Kiinteistöt
    "real_property": {
        "source_dsn_setting_name": "AREA_DATABASE_DSN",
        "source_name": "Kiinteistö: Kiinteistöalue",
        "source_identifier": "kiinteisto.kiinteisto_alue_alueet",
        "area_type": AreaType.REAL_PROPERTY,
        "identifier_field_name": "kiinteistotunnus",
        "metadata_columns": [
            "kiinteistotunnus",
            "pintaala",
            "rekisterointipvm",
            "kumoamispvm",
            "rekisterilaji_tunnus",
            "rekisterilaji_selite",
            "kayttotark_tunnus",
            "kayttotark_selite",
            "olotila_tunnus",
            "olotila_selite",
        ],
        "query": """
        SELECT *, ST_AsText(ST_CollectionExtract(ST_MakeValid(ST_Transform(ST_CurveToLine(a.geom), 4326)), 3))
            AS geom_text
        FROM kiinteisto.kiinteisto_alue_alueet AS a
        WHERE kiinteistotunnus IS NOT NULL
        """,
    },
    # Määräalat
    "unseparated_parcel": {
        "source_dsn_setting_name": "AREA_DATABASE_DSN",
        "source_name": "Kiinteistö: Määräala",
        "source_identifier": "kiinteisto.maaraala_alue_alueet",
        "area_type": AreaType.UNSEPARATED_PARCEL,
        "identifier_field_name": "maaraalatunnus",
        "metadata_columns": [
            "maaraalatunnus",
            "pintaala",
            "rekisterointipvm",
            "saantopvm",
            "laatu_tunnus",
            "laatu_selite",
            "tyyppi_tunnus",
            "tyyppi_selite",
            "olotila_tunnus",
            "olotila_selite",
        ],
        "query": """
        SELECT *, ST_AsText(ST_CollectionExtract(ST_MakeValid(ST_Transform(ST_CurveToLine(a.geom), 4326)), 3))
            AS geom_text
        FROM kiinteisto.maaraala_alue_alueet AS a
        WHERE maaraalatunnus IS NOT NULL
        """,
    },
    # Kaavayksiköt
    "plan_unit": {
        "source_dsn_setting_name": "AREA_DATABASE_DSN",
        "source_name": "Kaava: Kaavayksiköt",
        "source_identifier": "kaava.kaavayksikot_alueet",
        "area_type": AreaType.PLAN_UNIT,
        "identifier_field_name": "kaavayksikkotunnus",
        "metadata_columns": [
            "kaavayksikkotunnus",
            "kaavatunnus",
            "tyyppi",
            "luokka",
            "kayttotarkoitus",
            "rekisteriala",
        ],
        "query": """
        SELECT *, ST_AsText(ST_CollectionExtract(ST_MakeValid(ST_Transform(ST_CurveToLine(a.geom), 4326)), 3))
            AS geom_text
        FROM kaava.kaavayksikot_alueet AS a
        WHERE kaavayksikkotunnus IS NOT NULL
        """,
    },
    # Tonttijaot
    "plot_division": {
        "source_dsn_setting_name": "AREA_DATABASE_DSN",
        "source_name": "Kaava: Tonttijako",
        "source_identifier": "kaava.tonttijako_alueet",
        "area_type": AreaType.PLOT_DIVISION,
        "identifier_field_name": "tonttijakotunnus",
        "metadata_columns": [
            "tonttijakotunnus",
            "hyvaksymispvm",
            "voimaantulopvm",
            "laji_tunnus",
            "laji_selite",
            "vaihe_tunnus",
            "vaihe_selite",
        ],
        "query": """
        SELECT *, ST_AsText(ST_CollectionExtract(ST_MakeValid(ST_Transform(ST_CurveToLine(a.geom), 4326)), 3))
            AS geom_text
        FROM kaava.tonttijako_alueet AS a
        WHERE tonttijakotunnus IS NOT NULL
        """,
    },
}


class AreaImporter(BaseImporter):
    type_name = "area"

    def __init__(self, stdout=None, stderr=None):
        self.stdout = stdout
        self.stderr = stderr
        self.area_types = None

    @classmethod
    def add_arguments(cls, parser):
        parser.add_argument(
            "--area-types",
            dest="area_types",
            type=str,
            required=False,
            help="comma separated list of area types to import (default: all)",
        )

    def read_options(self, options):
        if options["area_types"]:
            self.area_types = []
            for area_type in options["area_types"].split(","):
                if area_type not in AREA_IMPORT_TYPES.keys():
                    raise RuntimeError(
                        'Area import type "{}" doesn\'t exist'.format(area_type)
                    )

                self.area_types.append(area_type)

    def execute(self):  # NOQA C901
        func_start = perf_counter()

        if not self.area_types:
            self.area_types = AREA_IMPORT_TYPES.keys()

        errors = []

        for area_import_type in self.area_types:
            type_start = perf_counter()

            self.stdout.write(
                'Starting to import the area type "{}"...\n'.format(area_import_type)
            )

            area_import = AREA_IMPORT_TYPES[area_import_type]

            try:
                conn = psycopg2.connect(
                    getattr(settings, area_import["source_dsn_setting_name"]),
                    cursor_factory=psycopg2.extras.NamedTupleCursor,
                )
            except (psycopg2.ProgrammingError, psycopg2.OperationalError) as e:
                self.stderr.write(str(e))
                self.stderr.write(
                    'Could not connect to the database when importing area type "{}". DSN setting name "{}"'.format(
                        area_import_type, area_import["source_dsn_setting_name"]
                    )
                )
                continue

            cursor = conn.cursor()

            self.stdout.write(area_import["source_name"])
            (source, source_created) = AreaSource.objects.get_or_create(
                identifier=area_import["source_identifier"],
                defaults={"name": area_import["source_name"]},
            )

            try:
                cursor.execute(area_import["query"])
            except psycopg2.ProgrammingError as e:
                self.stderr.write(str(e))
                continue

            imported_identifiers = []
            count = 0
            sum_row_time, avg_row_time, min_row_time, max_row_time = (0,) * 4
            self.stdout.write("Starting to update areas...\n")
            for row in cursor:
                row_start = perf_counter()

                try:
                    metadata = {
                        METADATA_COLUMN_NAME_MAP[column_name]: getattr(row, column_name)
                        for column_name in area_import["metadata_columns"]
                    }
                except AttributeError as e:
                    errors.append(
                        "id #{}, metadata field missing. Error: {}\n".format(
                            row.id, str(e)
                        )
                    )

                    count += 1
                    self.stdout.write("E", ending="")
                    if count % 1000 == 0:
                        self.stdout.write(" {}".format(count))
                        self.stdout.flush()
                    continue

                areas = Area.objects.all()
                match_data = {
                    "type": area_import["area_type"],
                    "identifier": getattr(row, area_import["identifier_field_name"]),
                    "source": source,
                }

                if area_import["area_type"] == AreaType.LEASE_AREA:
                    match_data["external_id"] = row.id

                if area_import["area_type"] == AreaType.PLAN_UNIT:
                    dp_id = metadata.get("detailed_plan_identifier")
                    if not dp_id:
                        self.stderr.write(
                            "detailed_plan_identifier not found for area #{}".format(
                                match_data["identifier"]
                            )
                        )
                        continue
                    areas = areas.filter(metadata__detailed_plan_identifier=dp_id)

                try:
                    geom = geos.GEOSGeometry(row.geom_text)
                except geos.error.GEOSException as e:
                    errors.append("id #{} error: {}\n".format(row.id, str(e)))

                    count += 1
                    self.stdout.write("E", ending="")
                    if count % 1000 == 0:
                        self.stdout.write(" {}".format(count))
                        self.stdout.flush()
                    continue

                if geom and isinstance(geom, geos.Polygon):
                    geom = geos.MultiPolygon(geom)

                if geom and not isinstance(geom, geos.MultiPolygon):
                    errors.append(
                        'id #{} Error! Geometry is not a Multipolygon but "{}"\n'.format(
                            row.id, geom
                        )
                    )

                    count += 1
                    self.stdout.write("E", ending="")
                    if count % 1000 == 0:
                        self.stdout.write(" {}".format(count))
                        self.stdout.flush()
                    continue

                other_data = {"geometry": geom, "metadata": metadata}

                try:
                    areas.update_or_create(defaults=other_data, **match_data)
                except MultipleObjectsReturned:  # There should only be one object per identifier...
                    ext_id = other_data.pop("external_id")
                    # ...so we delete them all but spare the one with the correct external_id (if it happens to exist)
                    Area.objects.filter(**match_data).exclude(
                        external_id=ext_id
                    ).delete()
                    match_data["external_id"] = ext_id
                    Area.objects.update_or_create(defaults=other_data, **match_data)

                imported_identifiers.append(match_data["identifier"])

                count += 1
                if count % 100 == 0:
                    self.stdout.write(".", ending="")
                if count % 1000 == 0:
                    self.stdout.write(" {}".format(count))
                    self.stdout.flush()

                row_end = perf_counter()
                row_time = row_end - row_start
                sum_row_time += row_time
                min_row_time = (
                    row_time
                    if min_row_time == 0 or row_time < min_row_time
                    else min_row_time
                )
                max_row_time = row_time if row_time > max_row_time else max_row_time

            if count > 0:
                avg_row_time = sum_row_time / count

            self.stdout.write(
                "Updated area count {}. Execution time: {:.2f}s "
                "(Row time avg: {:.2f}s, min: {:.2f}s, max: {:.2f}s)\n".format(
                    count, sum_row_time, avg_row_time, min_row_time, max_row_time
                )
            )

            self.stdout.write("Starting to remove stales...\n")
            stale_time_start = perf_counter()
            stale = Area.objects.filter(
                type=area_import["area_type"], source=source
            ).exclude(identifier__in=imported_identifiers)
            stale_count = stale.count()
            stale.delete()
            stale_time_end = perf_counter()
            self.stdout.write(
                "Removed stale count {}. Execution time: {:.2f}s\n".format(
                    stale_count, stale_time_end - stale_time_start
                )
            )

            if errors:
                self.stdout.write(" {} errors:\n".format(len(errors)))
                for error in errors:
                    self.stdout.write(error)

            type_end = perf_counter()
            self.stdout.write(
                'The area import of type "{}" is completed. Execution time: {:.2f}s\n'.format(
                    area_import_type, (type_end - type_start)
                )
            )

        func_end = perf_counter()
        self.stdout.write(
            "The area import is completed. Execution time: {0:.2f}s\n".format(
                func_end - func_start
            )
        )
