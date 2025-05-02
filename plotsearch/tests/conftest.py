from pathlib import Path
from unittest.mock import patch

import pytest
from django.core.management import call_command
from django.test import override_settings

from leasing.enums import ServiceUnitId
from leasing.models.contact import Contact
from leasing.models.service_unit import ServiceUnit
from mvj.tests.test_urls import reload_urlconf
from plotsearch.enums import AreaSearchLessor


@pytest.fixture(scope="package", autouse=True)
def set_plotsearch_flag():
    """Set the FLAG_PLOTSEARCH to True before the package tests and False after the tests.
    Reloads urlconf after setting the flag.
    Allows running tests as if the feature was enabled.
    TODO: Remove this fixture when the feature flag is removed."""
    # Before any tests in package
    with override_settings(FLAG_PLOTSEARCH=True):
        reload_urlconf()
    yield
    # Tear down after the tests in package
    with override_settings(FLAG_PLOTSEARCH=False):
        reload_urlconf()


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    """Loads all the database fixtures in the plotsearch/fixtures and leasing/fixtures folder"""
    fixture_path = Path(__file__).parents[1] / "fixtures"
    fixture_filenames = [path for path in fixture_path.glob("*") if not path.is_dir()]

    with django_db_blocker.unblock():
        call_command("loaddata", *fixture_filenames)

    fixture_path = Path(__file__).parents[1].parent / "leasing/fixtures"
    fixture_filenames = [path for path in fixture_path.glob("*") if not path.is_dir()]

    with django_db_blocker.unblock():
        call_command("loaddata", *fixture_filenames)


@pytest.fixture
def setup_lessor_contacts_and_service_units(service_unit_factory, contact_factory):
    """
    Sets up lessor contacts and service units for testing.
    Should be used in all tests that call generate_and_queue_answer_emails.

    Normally, service units have specific known IDs, but during testing they are
    initialized with factories, so we need to align some logic to these dynamic
    IDs.
    """
    # Assumption: all service units are also area search lessors
    assert len(ServiceUnitId) == len(AreaSearchLessor)

    service_units: list[ServiceUnit] = []
    contacts: list[Contact] = []

    # Instantiate service units and lessor contacts via factories
    for unit_id in ServiceUnitId:
        unit = service_unit_factory(name=str(unit_id))
        service_units.append(unit)
        contacts.append(
            contact_factory(
                name=unit.name,
                service_unit=unit,
                is_lessor=True,
                email=f"{unit_id.name}@example.com",
            )
        )

    lessors_enum_list = list(AreaSearchLessor)
    mock_map = {
        lessor: service_units[i].pk for i, lessor in enumerate(lessors_enum_list)
    }

    def mock_map_lessor_enum_to_service_unit_id(lessor: AreaSearchLessor) -> int:
        """Maps an areasearch lessor to a service unit ID that was created via a factory."""
        return mock_map[lessor]

    with patch(
        "plotsearch.utils.map_lessor_enum_to_service_unit_id",
        side_effect=mock_map_lessor_enum_to_service_unit_id,
    ), patch(
        "plotsearch.tests.test_utils.map_lessor_enum_to_service_unit_id",
        side_effect=mock_map_lessor_enum_to_service_unit_id,
    ):
        yield
