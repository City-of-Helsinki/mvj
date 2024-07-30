import io
from collections import namedtuple

import pytest

from leasing.enums import AreaType
from leasing.importer.area import AreaImporter

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


def test_get_metadata():
    stdout = io.StringIO()
    area_importer = AreaImporter(stdout=stdout)
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

    metadata, error_count = area_importer.get_metadata(
        row, AREA_IMPORT, COLUMN_NAME_MAP, [], 0
    )
    assert metadata["first_column_mapped"] == first_column_value
    assert metadata["second_column_mapped"] == second_column_value

    RowIncorrect = namedtuple(
        "RowIncorrect",
        [
            "id",
            "third_column",
        ],
    )
    row_incorrect = RowIncorrect(
        id=id,
        third_column="4321",
    )

    # Should be missing "first_column"
    metadata, error_count = area_importer.get_metadata(
        row_incorrect, AREA_IMPORT, COLUMN_NAME_MAP, [], 0
    )
    assert error_count == 1, "Should have one error as function exists on first error"
    stdout_value = stdout.getvalue()
    assert "E" in stdout_value

    stdout.close()
