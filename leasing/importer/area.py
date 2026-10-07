import logging
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from time import perf_counter
from typing import (
    Any,
    Dict,
    LiteralString,
    NotRequired,
    Optional,
    Tuple,
    TypedDict,
    cast,
)

import psycopg
from django.conf import settings
from django.contrib.gis import geos
from django.contrib.gis.geos.error import GEOSException
from django.core.exceptions import MultipleObjectsReturned
from django.db import IntegrityError
from django.db.models import QuerySet
from psycopg import sql
from psycopg.rows import namedtuple_row

from leasing.enums import AreaType
from leasing.models.area import Area, AreaSource

from .base import BaseImporter

logger = logging.getLogger(__name__)

Metadata = Dict[str, Any]


class AreaImport(TypedDict):
    source_dsn_setting_name: str
    source_name: str
    source_identifier: str
    area_type: AreaType
    identifier_field_name: str
    metadata_columns: list[str]
    query: LiteralString


MatchDataIdentifier = Any


class MatchData(TypedDict):
    type: AreaType
    identifier: MatchDataIdentifier
    source: AreaSource
    external_id: NotRequired[Any]
    detailed_plan_identifier: NotRequired[Optional[str]]


class UpdateData(TypedDict):
    geometry: geos.MultiPolygon
    metadata: Metadata
    external_id: NotRequired[Any]


@dataclass
class AreaImportCounters:
    processed: int = 0
    created: int = 0
    updated: int = 0
    skipped: int = 0
    failed: int = 0

    @property
    def persisted(self) -> int:
        return self.created + self.updated


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
    "kaavanumero": "detailed_plan_identifier",
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


AREA_IMPORT_TYPES: Dict[str, AreaImport] = {
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
        "identifier_field_name": "kaavanumero",
        "metadata_columns": [
            "kaavanumero",
            "diaarinumero",
            "kaavavaihe",
            "hyvaksyja",
        ],  # noqa: E231
        "query": """
        SELECT *, ST_AsText(ST_CollectionExtract(ST_MakeValid(ST_Transform(ST_CurveToLine(a.geom), 4326)), 3))
            AS geom_text
        FROM maka.hankerajaus_alue_kaavahanke AS a
        WHERE kaavanumero IS NOT NULL
        """,
    },
    # Vuokra-alueet: MAKE / vuokrausalue_paa
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
    # Vuokra-alueet: KAMA & KUVA / vuokrausalue_lyhyt_paa
    "lease_area_kama_kuva": {
        "source_dsn_setting_name": "KAMA_KUVA_LEASE_AREA_DATABASE_DSN",
        "source_name": "Tonttiosasto: vuokrausalue_lyhyt_paa",
        "source_identifier": "tonttiosasto.vuokrausalue_lyhyt_paa",
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
        FROM tonttiosasto.vuokrausalue_lyhyt_paa AS a
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

    def __init__(self, stdout: Any = None, stderr: Any = None) -> None:
        self.stdout = stdout
        self.stderr = stderr
        self.area_types: list[str] = []

    @classmethod
    def add_arguments(cls, parser: Any) -> None:
        parser.add_argument(
            "--area-types",
            dest="area_types",
            type=str,
            required=False,
            help="comma separated list of area types to import (default: all)",
        )

    def read_options(self, options: Mapping[str, Any]) -> None:
        if options["area_types"]:
            self.area_types = []
            for area_type in options["area_types"].split(","):
                if area_type not in AREA_IMPORT_TYPES.keys():
                    raise RuntimeError(f'Area import type "{area_type}" doesn\'t exist')

                self.area_types.append(area_type)

    def get_database_connection(
        self, area_import: AreaImport, area_import_type: str
    ) -> Optional[psycopg.Connection[Any]]:
        try:
            conn = psycopg.connect(
                getattr(settings, area_import["source_dsn_setting_name"]),
                row_factory=namedtuple_row,
            )
            return conn
        except (psycopg.ProgrammingError, psycopg.OperationalError) as e:
            self.stderr.write(str(e))
            source_dsn_setting_name = area_import["source_dsn_setting_name"]
            error_msg = (
                f'Could not connect to the database when importing area type "{area_import_type}". '
                f'DSN setting name "{source_dsn_setting_name}"'
            )
            self.stderr.write(error_msg)
            # Use logger to trigger sentry capturing
            logger.error(error_msg)
            return None

    def execute(self) -> None:
        func_start = perf_counter()

        if not self.area_types:
            self.area_types = list(AREA_IMPORT_TYPES.keys())

        for area_import_type in self.area_types:
            self.process_area_import_type(area_import_type)

        func_end = perf_counter()
        self.stdout.write(
            f"The area import is completed. Execution time: {func_end - func_start:.2f}s\n"
        )

    def get_metadata(
        self,
        row: Any,
        area_import: AreaImport,
        column_name_map: Dict[str, str],
        error_messages: list[str],
        failure_count: int,
    ) -> Tuple[Optional[Metadata], int]:
        try:
            metadata: Metadata = {
                column_name_map[column_name]: getattr(row, column_name)
                for column_name in area_import["metadata_columns"]
            }
            return metadata, failure_count
        except AttributeError as e:
            error_messages.append(
                f"id #{row.id}, metadata field missing. Error: {str(e)}\n"
            )

            failure_count += 1
            self.stdout.write("E")
            if failure_count % 1000 == 0:
                self.stdout.write(f" {failure_count}")
                self.stdout.flush()
            return None, failure_count

    def get_match_data(
        self,
        row: Any,
        area_import: AreaImport,
        source: AreaSource,
    ) -> MatchData:
        match_data: MatchData = {
            "type": area_import["area_type"],
            "identifier": getattr(row, area_import["identifier_field_name"]),
            "source": source,
        }

        if area_import["area_type"] == AreaType.LEASE_AREA:
            match_data["external_id"] = row.id

        return match_data

    def get_update_data(
        self,
        row: Any,
        metadata: Metadata,
        geom: geos.MultiPolygon,
    ) -> UpdateData:
        update_data: UpdateData = {
            "geometry": geom,
            "metadata": metadata,
        }

        ext_id = getattr(row, "id", None)

        if ext_id is not None:
            update_data["external_id"] = ext_id

        return update_data

    def get_plan_unit_areas(
        self, metadata: Metadata, identifier: MatchDataIdentifier
    ) -> Optional[QuerySet[Area]]:
        areas = Area.objects.all()
        dp_id = metadata.get("detailed_plan_identifier")
        if dp_id is None:
            self.stderr.write(
                f"detailed_plan_identifier not found for area #{identifier}"
            )
            return None

        return cast(
            QuerySet[Area],
            areas.filter(metadata__detailed_plan_identifier=dp_id),
        )

    def get_geometry(
        self, row: Any, error_messages: list[str], failure_count: int
    ) -> Tuple[Optional[geos.GEOSGeometry], int]:
        try:
            geom = geos.GEOSGeometry(row.geom_text)
            return geom, failure_count
        except GEOSException as e:
            error_messages.append(f"id #{row.id} error: {str(e)}\n")

            failure_count += 1
            self.stdout.write("E")
            if failure_count % 1000 == 0:
                self.stdout.write(f" {failure_count}")
                self.stdout.flush()
            return None, failure_count

    def handle_geometry(
        self,
        geom: geos.GEOSGeometry,
        row: Any,
        error_messages: list[str],
        failure_count: int,
    ) -> Tuple[Optional[geos.MultiPolygon], int]:
        if geom and isinstance(geom, geos.Polygon):
            geom = geos.MultiPolygon(geom)

        if geom and not isinstance(geom, geos.MultiPolygon):
            error_messages.append(
                f'id #{row.id} Error! Geometry is not a Multipolygon but "{geom}"\n'
            )

            failure_count += 1
            self.stdout.write("E")
            if failure_count % 1000 == 0:
                self.stdout.write(f" {failure_count}")
                self.stdout.flush()
            return None, failure_count

        return cast(geos.MultiPolygon, geom), failure_count

    def update_or_create_areas(
        self,
        areas: QuerySet[Area],
        update_data: UpdateData,
        match_data: MatchData,
        imported_identifiers: list[str],
    ) -> Tuple[list[str], Optional[bool]]:
        created = None
        try:
            _, created = areas.update_or_create(
                defaults=dict(update_data), **match_data
            )
        except (
            MultipleObjectsReturned,
            IntegrityError,
        ):  # There should only be one object per identifier...
            ext_id = (
                update_data["external_id"] if "external_id" in update_data else None
            )
            # If external id exists, we can continue deleting data. We should only
            # delete duplicate rows, if we have external id available for the new row.
            if ext_id:
                # ...so we delete them all but spare the one with the correct
                # external_id (if it happens to exist)
                Area.objects.filter(**match_data).exclude(external_id=ext_id).delete()
                match_data["external_id"] = ext_id
                _, created = Area.objects.update_or_create(
                    defaults=dict(update_data), **match_data
                )

        imported_identifiers.append(match_data["identifier"])
        return imported_identifiers, created

    def record_persistence_result(
        self, counters: AreaImportCounters, created: Optional[bool]
    ) -> None:
        if created is True:
            counters.created += 1
        elif created is False:
            counters.updated += 1
        else:
            counters.failed += 1
            return

        if counters.persisted % 100 == 0 and counters.persisted > 0:
            self.stdout.write(".")
        if counters.persisted % 1000 == 0 and counters.persisted > 0:
            self.stdout.write(f" {counters.persisted}")
            self.stdout.flush()

    def process_rows(
        self,
        cursor: Iterable[Any],
        area_import: AreaImport,
        source: AreaSource,
        error_messages: list[str],
    ) -> list[str]:
        imported_identifiers: list[str] = []
        counters = AreaImportCounters()
        sum_row_time, avg_row_time, min_row_time, max_row_time = (0.0,) * 4
        self.stdout.write("Starting to update areas...\n")
        for row in cursor:
            counters.processed += 1
            row_start = perf_counter()

            metadata, failure_count = self.get_metadata(
                row,
                area_import,
                METADATA_COLUMN_NAME_MAP,
                error_messages,
                counters.failed,
            )
            counters.failed = failure_count
            if metadata is None:
                continue

            match_data = self.get_match_data(row, area_import, source)

            areas = Area.objects.all()

            if area_import["area_type"] == AreaType.PLAN_UNIT:
                if not metadata.get("detailed_plan_identifier"):
                    counters.skipped += 1
                    continue
                areas = self.get_plan_unit_areas(metadata, match_data["identifier"])
                if areas is None:
                    counters.skipped += 1
                    continue

            geom, failure_count = self.get_geometry(
                row, error_messages, counters.failed
            )
            counters.failed = failure_count
            if geom is None:
                continue

            geom, failure_count = self.handle_geometry(
                geom, row, error_messages, counters.failed
            )
            counters.failed = failure_count
            if geom is None:
                continue

            update_data: UpdateData = self.get_update_data(row, metadata, geom)

            imported_identifiers, created = self.update_or_create_areas(
                areas, update_data, match_data, imported_identifiers
            )
            self.record_persistence_result(counters, created)

            row_end = perf_counter()
            row_time = row_end - row_start
            sum_row_time += row_time
            min_row_time = (
                row_time
                if min_row_time == 0 or row_time < min_row_time
                else min_row_time
            )
            max_row_time = row_time if row_time > max_row_time else max_row_time

        if counters.persisted > 0:
            avg_row_time = sum_row_time / counters.persisted

        self.stdout.write(
            f"Processed {counters.processed} areas: created {counters.created}, "
            f"updated {counters.updated}, skipped {counters.skipped}, "
            f"failed {counters.failed}. Execution time: {sum_row_time:.2f}s "
            f"(Row time avg: {avg_row_time:.2f}s, min: {min_row_time:.2f}s, max: {max_row_time:.2f}s)\n"
        )
        return imported_identifiers

    def process_area_import_type(self, area_import_type: str) -> None:
        type_start = perf_counter()

        error_messages: list[str] = []
        self.stdout.write(f'Starting to import the area type "{area_import_type}"...\n')

        area_import = AREA_IMPORT_TYPES[area_import_type]

        conn = self.get_database_connection(area_import, area_import_type)
        if conn is None:
            return

        cursor = conn.cursor(row_factory=namedtuple_row)

        self.stdout.write(area_import["source_name"])
        source, _ = AreaSource.objects.get_or_create(
            identifier=area_import["source_identifier"],
            defaults={"name": area_import["source_name"]},
        )

        try:
            cursor.execute(sql.SQL(area_import["query"]))
        except psycopg.ProgrammingError as e:
            self.stderr.write(str(e))
            logger.error(str(e))
            return

        imported_identifiers = self.process_rows(
            cursor, area_import, source, error_messages
        )
        self.handle_stale_areas(area_import, source, imported_identifiers)

        if error_messages:
            self.stdout.write(f" {len(error_messages)} errors:\n")
            for error_message in error_messages:
                self.stdout.write(error_message)

            # Use logger to trigger sentry capturing
            logger.error(f"Errors occurred during area import: {len(error_messages)}")

        type_end = perf_counter()
        self.stdout.write(
            f'The area import of type "{area_import_type}" is completed. Execution time: {type_end - type_start:.2f}s\n'
        )

    def handle_stale_areas(
        self,
        area_import: AreaImport,
        source: AreaSource,
        imported_identifiers: list[str],
    ) -> None:
        self.stdout.write("Starting to remove stales...\n")
        stale_time_start = perf_counter()
        stale = Area.objects.filter(
            type=area_import["area_type"], source=source
        ).exclude(identifier__in=imported_identifiers)
        stale_count = stale.count()
        stale.delete()
        stale_time_end = perf_counter()
        self.stdout.write(
            f"Removed stale count {stale_count}. Execution time: {stale_time_end - stale_time_start:.2f}s\n"
        )
