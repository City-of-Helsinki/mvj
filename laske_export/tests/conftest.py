import tempfile

import pytest
from django.conf import settings

from leasing.tests.conftest import *  # noqa


def pytest_configure():
    laske_export_root = tempfile.mkdtemp(prefix="laske-export-")
    settings.LANGUAGE_CODE = "en"
    settings.LASKE_EXPORT_ROOT = laske_export_root
    settings.LASKE_SERVERS = {
        "export": {"host": "localhost", "username": "test", "password": "test"}
    }


@pytest.fixture(scope="function", autouse=True)
def laske_export_from_email(override_config):
    with override_config(LASKE_EXPORT_FROM_EMAIL="john@example.com"):
        yield


@pytest.fixture(scope="function", autouse=True)
def laske_export_announce_email(override_config):
    with override_config(
        LASKE_EXPORT_ANNOUNCE_EMAIL="john@example.com,jane@example.com"
    ):
        yield
