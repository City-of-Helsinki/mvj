import io
from collections import namedtuple
from types import SimpleNamespace
from typing import Callable
from unittest.mock import MagicMock

import pytest
from django.contrib.gis import geos

from leasing.enums import AreaType
from leasing.importer.area import AreaImporter
from leasing.models.area import Area, AreaSource

AREA_IMPORT = {
    "source_dsn_setting_name": "LEASE_AREA_DATABASE_DSN",
    "source_name": "Tonttiosasto: vuokrausalue_paa",
    "source_identifier": "tonttiosasto.vuokrausalue_paa",
    "area_type": AreaType.LEASE_AREA,
    "identifier_field_name": "vuokratunnus",
    "metadata_columns": [
        "first_column",
        "second_column",
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
}

COLUMN_NAME_MAP = {
    "first_column": "first_column_mapped",
    "second_column": "second_column_mapped",
}


@pytest.fixture
def area_importer():
    stdout = io.StringIO()
    stderr = io.StringIO()
    return AreaImporter(stdout=stdout, stderr=stderr)


def test_read_options_selects_requested_area_types(area_importer):
    area_importer.read_options({"area_types": "lease_area,plan_unit"})
    assert area_importer.area_types == ["lease_area", "plan_unit"]


def test_read_options_rejects_unknown_area_type(area_importer):
    with pytest.raises(RuntimeError, match='Area import type "unknown" doesn\'t exist'):
        area_importer.read_options({"area_types": "unknown"})


def test_get_metadata_maps_configured_columns(area_importer):
    AreaRow = namedtuple(
        "Row",
        [
            "id",
            "first_column",
            "second_column",
        ],
    )
    id = 5
    first_column_value = "4321"
    second_column_value = "1234"
    row = AreaRow(
        id=id,
        first_column=first_column_value,
        second_column=second_column_value,
    )

    metadata, failure_count = area_importer.get_metadata(
        row, AREA_IMPORT, COLUMN_NAME_MAP, [], 0
    )
    assert metadata == {
        "first_column_mapped": first_column_value,
        "second_column_mapped": second_column_value,
    }
    assert failure_count == 0


def test_get_metadata_reports_missing_source_column(area_importer):
    error_messages = []
    row = SimpleNamespace(id=5, third_column="4321")

    metadata, failure_count = area_importer.get_metadata(
        row, AREA_IMPORT, COLUMN_NAME_MAP, error_messages, 0
    )

    assert metadata is None
    assert failure_count == 1
    assert len(error_messages) == 1
    assert "id #5, metadata field missing" in error_messages[0]
    assert "first_column" in error_messages[0]
    assert area_importer.stdout.getvalue() == "E"


@pytest.mark.parametrize(
    ("area_type", "expected_external_id"),
    [
        (AreaType.LEASE_AREA, "source-123"),
        (AreaType.REAL_PROPERTY, None),
    ],
)
def test_get_match_data_uses_external_id_only_for_lease_areas(
    area_importer, area_type, expected_external_id
):
    source = MagicMock()
    area_import = dict(AREA_IMPORT, area_type=area_type)
    row = SimpleNamespace(id="source-123", vuokratunnus="lease-456")

    match_data = area_importer.get_match_data(row, area_import, source)

    assert match_data["type"] == area_type
    assert match_data["identifier"] == "lease-456"
    assert match_data["source"] is source
    if expected_external_id is None:
        assert "external_id" not in match_data
    else:
        assert match_data["external_id"] == expected_external_id


def test_get_update_data_contains_geometry_metadata_and_external_id(area_importer):
    geometry = geos.MultiPolygon(
        geos.Polygon(((0, 0), (0, 1), (1, 1), (0, 0))), srid=4326
    )
    metadata = {"area": "1"}

    update_data = area_importer.get_update_data(
        SimpleNamespace(id="source-123"), metadata, geometry
    )
    assert update_data == {
        "geometry": geometry,
        "metadata": metadata,
        "external_id": "source-123",
    }


def test_get_geometry_parses_valid_wkt(area_importer):
    geometry, failure_count = area_importer.get_geometry(
        SimpleNamespace(id=1, geom_text="MULTIPOLYGON (((0 0, 0 1, 1 1, 0 0)))"),
        [],
        0,
    )
    assert isinstance(geometry, geos.MultiPolygon)
    assert failure_count == 0


def test_get_geometry_reports_geos_error(area_importer, monkeypatch):
    error_messages = []
    monkeypatch.setattr(
        "leasing.importer.area.geos.GEOSGeometry",
        MagicMock(side_effect=geos.GEOSException("Invalid geometry")),
    )

    geometry, failure_count = area_importer.get_geometry(
        SimpleNamespace(id=7, geom_text="POLYGON EMPTY"), error_messages, 0
    )
    assert geometry is None
    assert failure_count == 1
    assert error_messages and error_messages[0].startswith("id #7 error:")
    assert area_importer.stdout.getvalue() == "E"


def test_handle_geometry_promotes_polygon_to_multipolygon(area_importer):
    polygon = geos.Polygon(((0, 0), (0, 1), (1, 1), (0, 0)), srid=4326)

    geometry, failure_count = area_importer.handle_geometry(
        polygon, SimpleNamespace(id=1), [], 0
    )
    assert isinstance(geometry, geos.MultiPolygon)
    assert failure_count == 0


def test_handle_geometry_rejects_non_polygonal_geometry(area_importer):
    error_messages = []

    geometry, failure_count = area_importer.handle_geometry(
        geos.Point(0, 0, srid=4326),
        SimpleNamespace(id=8),
        error_messages,
        0,
    )
    assert geometry is None
    assert failure_count == 1
    assert error_messages and "Geometry is not a Multipolygon" in error_messages[0]
    assert area_importer.stdout.getvalue() == "E"


def test_get_plan_unit_areas_filters_by_detailed_plan_identifier(
    area_importer, monkeypatch
):
    areas = MagicMock()
    monkeypatch.setattr("leasing.importer.area.Area.objects.all", lambda: areas)

    result = area_importer.get_plan_unit_areas(
        {"detailed_plan_identifier": "12345"}, "plan-unit-1"
    )
    assert result is areas.filter.return_value
    areas.filter.assert_called_once_with(metadata__detailed_plan_identifier="12345")


def test_update_or_create_areas_persists_valid_area(area_importer):
    areas = MagicMock()
    geometry = geos.MultiPolygon(
        geos.Polygon(((0, 0), (0, 1), (1, 1), (0, 0))), srid=4326
    )
    update_data = {
        "geometry": geometry,
        "metadata": {"area": "1"},
        "external_id": "source-123",
    }
    match_data = {
        "type": AreaType.LEASE_AREA,
        "identifier": "lease-456",
        "source": MagicMock(),
        "external_id": "source-123",
    }

    areas.update_or_create.return_value = (MagicMock(), True)

    imported_identifiers, created = area_importer.update_or_create_areas(
        areas, update_data, match_data, []
    )
    areas.update_or_create.assert_called_once_with(
        defaults=dict(update_data), **match_data
    )
    assert imported_identifiers == ["lease-456"]
    assert created is True


def test_process_rows_reports_separate_counters(area_importer, monkeypatch):
    area_import = dict(AREA_IMPORT, metadata_columns=["sopimusnumero"])
    rows = [
        SimpleNamespace(
            id="source-1",
            vuokratunnus="lease-1",
            sopimusnumero="contract-1",
            geom_text="MULTIPOLYGON (((0 0, 0 1, 1 1, 0 0)))",
        ),
        SimpleNamespace(
            id="source-2",
            vuokratunnus="lease-2",
            sopimusnumero="contract-2",
            geom_text="MULTIPOLYGON (((0 0, 0 1, 1 1, 0 0)))",
        ),
        SimpleNamespace(id="source-3", vuokratunnus="lease-3"),
    ]
    areas = MagicMock()
    areas.update_or_create.side_effect = [(MagicMock(), True), (MagicMock(), False)]
    monkeypatch.setattr("leasing.importer.area.Area.objects.all", lambda: areas)

    imported_identifiers = area_importer.process_rows(
        rows, area_import, MagicMock(), []
    )

    assert imported_identifiers == ["lease-1", "lease-2"]
    assert (
        "Processed 3 areas: created 1, updated 1, skipped 0, failed 1."
        in area_importer.stdout.getvalue()
    )


@pytest.mark.django_db
def test_handle_stale_areas_only_deletes_in_same_type_and_source(
    area_importer,
    area_factory: Callable[..., Area],
    area_source_factory: Callable[..., AreaSource],
):
    target_source = area_source_factory(
        identifier="target-source",
        name="Target source",
    )
    other_source = area_source_factory(
        identifier="other-source",
        name="Other source",
    )
    imported = area_factory(
        type=AreaType.LEASE_AREA,
        identifier="imported",
        external_id="1",
        source=target_source,
    )
    same_type_and_source = area_factory(
        type=AreaType.LEASE_AREA,
        identifier="not-imported",
        external_id="2",
        source=target_source,
    )
    same_source_different_type = area_factory(
        type=AreaType.PLAN_UNIT,
        identifier="not-imported",
        external_id="3",
        source=target_source,
    )
    same_type_different_source = area_factory(
        type=AreaType.LEASE_AREA,
        identifier="not-imported",
        external_id="4",
        source=other_source,
    )
    area_importer.handle_stale_areas(AREA_IMPORT, target_source, [imported.identifier])

    assert Area.objects.filter(pk=imported.pk).exists()
    assert not Area.objects.filter(pk=same_type_and_source.pk).exists()
    assert Area.objects.filter(pk=same_source_different_type.pk).exists()
    assert Area.objects.filter(pk=same_type_different_source.pk).exists()
