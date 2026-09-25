from django.conf import settings


def pytest_configure():
    """Overwrite invoicing settings to avoid mistakes during testing."""
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
