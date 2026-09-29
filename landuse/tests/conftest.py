import pytest


@pytest.fixture(autouse=True)
def block_landuse_external_services(settings):
    """Prevent land-use tests from using real invoicing integrations."""
    settings.FLAG_LANDUSE_SAP_EXPORT_ENABLED = False
    settings.SAP_LANDUSE_VALUES = None
    settings.LANDUSE_SAP_EXPORT_DIRECTORY = "/blocked-in-tests"
    settings.LASKE_SERVERS = {
        "landuse_export": {
            "host": "127.0.0.1",
            "port": 1,
            "username": "blocked-in-tests",
            "password": "blocked-in-tests",
            "directory": "/blocked-in-tests",
            "key_type": "rsa",
            "key": b"blocked-in-tests",
        },
        "landuse_payments": {
            "host": "127.0.0.1",
            "port": 1,
            "username": "blocked-in-tests",
            "password": "blocked-in-tests",
            "directory": "/blocked-in-tests",
            "key_type": "rsa",
            "key": b"blocked-in-tests",
        },
    }
