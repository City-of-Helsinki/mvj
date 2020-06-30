import tempfile

from django.conf import settings

from leasing.tests.conftest import *  # noqa


def pytest_configure():
    laske_export_root = tempfile.mkdtemp(prefix="laske-export-")
    settings.LASKE_EXPORT_ROOT = laske_export_root
    settings.LASKE_SERVERS = {
        "export": {"host": "localhost", "username": "test", "password": "test"}
    }
