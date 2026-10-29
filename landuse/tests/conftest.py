import pytest


@pytest.fixture
def tab_role_user(user_factory, group_factory):
    from landuse.permissions import LANDUSE_GROUP_MODEL_PERMISSIONS
    from utils.management.commands.set_group_model_permissions import (
        get_group_permissions,
        get_permissions_by_codename,
    )

    def create_user(role):
        group = group_factory()
        for model, config in LANDUSE_GROUP_MODEL_PERMISSIONS.items():
            assignments = get_group_permissions(
                {role: group},
                model,
                {role: config["model"].get(role)},
                get_permissions_by_codename(model),
            )
            group.permissions.add(
                *(assignment.permission for assignment in assignments)
            )
        user = user_factory(is_superuser=False)
        user.groups.set([group])
        return user

    return create_user


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
