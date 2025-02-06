from pathlib import Path

import pytest
from django.core.management import call_command
from django.test import override_settings

from mvj.tests.test_urls import reload_urlconf


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
