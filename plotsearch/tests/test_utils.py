from unittest.mock import patch

import pytest

from leasing.enums import ServiceUnitId
from leasing.models.service_unit import ServiceUnit
from plotsearch.enums import AreaSearchLessor
from plotsearch.utils import (
    map_intended_use_to_service_unit_id,
    map_lessor_enum_to_service_unit_id,
)


@pytest.fixture
def setup_service_unit_mocks(service_unit_factory):
    """
    Normally, service units have specific known IDs, but during testing they are
    initialized with factories, so we need to align some mappings to these
    dynamic IDs.
    """
    # Assumption: all service units are also area search lessors
    assert len(ServiceUnitId) == len(AreaSearchLessor)

    service_units: list[ServiceUnit] = []

    service_units = [
        service_unit_factory(name=str(unit_id)) for unit_id in ServiceUnitId
    ]

    def mock_map_lessor_enum_to_service_unit_id(lessor: AreaSearchLessor) -> int:
        """Maps an areasearch lessor to a service unit ID that was created via a factory."""
        lessors_enum_list = list(AreaSearchLessor)
        mock_map = {
            lessor: service_units[i].pk for i, lessor in enumerate(lessors_enum_list)
        }
        return mock_map[lessor]

    with patch(
        "plotsearch.utils.map_lessor_enum_to_service_unit_id",
        side_effect=mock_map_lessor_enum_to_service_unit_id,
    ), patch(
        "plotsearch.tests.test_utils.map_lessor_enum_to_service_unit_id",
        side_effect=mock_map_lessor_enum_to_service_unit_id,
    ):
        yield


@pytest.mark.parametrize(
    "intended_use_name,lessor",
    [
        ("Ravitsemus, myynti ja mainonta", "AKV"),
        ("Taide ja kulttuuri", "AKV"),
        ("Varastointi ja jakelu", "AKV"),
        ("Työmaat", "AKV"),
        ("Muu alueen käyttö", "MAKE"),
        ("Veneily ja laiturit", "UPA"),
        ("Urheilu ja Liikunta", "LIPA"),
    ],
)
@pytest.mark.django_db
def test_map_intended_use_to_service_unit_id(
    intended_use_name,
    lessor,
    setup_service_unit_mocks,
    area_search_intended_use_factory,
):
    """Test that the intended use maps to the correct service unit ID."""

    intended_use = area_search_intended_use_factory(
        name=intended_use_name, name_fi=intended_use_name
    )
    assert map_intended_use_to_service_unit_id(
        intended_use
    ) == map_lessor_enum_to_service_unit_id(lessor)
