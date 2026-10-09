from io import StringIO
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management import call_command

from utils.management.commands import set_group_model_permissions


def make_model(app_label, model_name, custom_permissions=()):
    return SimpleNamespace(
        _meta=SimpleNamespace(
            app_label=app_label,
            model_name=model_name,
            permissions=tuple(
                (codename, f"Can {codename}") for codename in custom_permissions
            ),
        )
    )


def create_permissions(app_label, model_name, custom_permissions=()):
    content_type, _ = ContentType.objects.get_or_create(
        app_label=app_label, model=model_name
    )
    permissions = {}
    for permission_type in set_group_model_permissions.PERMISSION_TYPES:
        codename = f"{permission_type}_{model_name}"
        permissions[codename], _ = Permission.objects.get_or_create(
            content_type=content_type,
            codename=codename,
            defaults={"name": f"Can {permission_type} {model_name}"},
        )
    for codename in custom_permissions:
        permissions[codename], _ = Permission.objects.get_or_create(
            content_type=content_type,
            codename=codename,
            defaults={"name": f"Can {codename}"},
        )
    return permissions


def configure_models(monkeypatch, models_by_app):
    monkeypatch.setattr(
        set_group_model_permissions.apps,
        "get_app_config",
        lambda app_name: SimpleNamespace(
            get_models=lambda include_auto_created: models_by_app.get(app_name, [])
        ),
    )


@pytest.mark.django_db
def test_permissions_for_identically_named_models_are_separated_by_app(monkeypatch):
    """Keep permissions distinct when different apps use the same model name."""

    model_name = "duplicatemodel"
    app_labels = ("credit_integration", "leasing")
    models_by_app = {
        app_label: [make_model(app_label, model_name)] for app_label in app_labels
    }

    for app_label in app_labels:
        create_permissions(app_label, model_name)

    group = Group.objects.create(id=1, name="Test group")
    monkeypatch.setattr(
        set_group_model_permissions,
        "DEFAULT_APP_PERMS",
        {
            app_label: {
                model_name: {set_group_model_permissions.UG.SELAILIJA: ("view",)}
            }
            for app_label in app_labels
        },
    )
    configure_models(monkeypatch, models_by_app)

    with patch.object(Group.permissions.through.objects, "bulk_create") as bulk_create:
        call_command("set_group_model_permissions")

    created_permissions = bulk_create.call_args.args[0]
    assigned_app_labels = {
        group_permission.permission.content_type.app_label
        for group_permission in created_permissions
        if group_permission.group_id == group.pk
    }
    assert assigned_app_labels == set(app_labels)


@pytest.mark.django_db
def test_assigns_configured_standard_and_custom_permissions(monkeypatch):
    """The happy path test."""
    app_label = "leasing"
    model_name = "permissiontestmodel"
    custom_permission = "approve_permissiontestmodel"
    model = make_model(app_label, model_name, (custom_permission,))
    permissions = create_permissions(app_label, model_name, (custom_permission,))
    viewer = Group.objects.create(id=1, name="Viewer")
    administrator = Group.objects.create(id=7, name="Administrator")

    monkeypatch.setattr(
        set_group_model_permissions,
        "DEFAULT_APP_PERMS",
        {
            app_label: {
                model_name: {
                    set_group_model_permissions.UG.SELAILIJA: None,
                    set_group_model_permissions.UG.PAAKAYTTAJA: (
                        "view",
                        "change",
                        custom_permission,
                    ),
                }
            }
        },
    )
    configure_models(monkeypatch, {app_label: [model]})

    call_command("set_group_model_permissions")

    assert not viewer.permissions.filter(
        content_type__app_label=app_label,
        content_type__model=model_name,
    ).exists()
    assert set(administrator.permissions.values_list("codename", flat=True)) == {
        permissions[f"view_{model_name}"].codename,
        permissions[f"change_{model_name}"].codename,
        custom_permission,
    }


@pytest.mark.django_db
def test_resolves_custom_permission_prefix_with_model_name(monkeypatch):
    app_label = "leasing"
    model_name = "lease"
    custom_permission = "delete_nonempty_lease"
    model = make_model(app_label, model_name, (custom_permission,))
    create_permissions(app_label, model_name, (custom_permission,))
    administrator = Group.objects.create(id=7, name="Administrator")

    monkeypatch.setattr(
        set_group_model_permissions,
        "DEFAULT_APP_PERMS",
        {
            app_label: {
                model_name: {
                    set_group_model_permissions.UG.PAAKAYTTAJA: ("delete_nonempty",)
                }
            }
        },
    )
    configure_models(monkeypatch, {app_label: [model]})

    call_command("set_group_model_permissions")

    assert list(administrator.permissions.values_list("codename", flat=True)) == [
        custom_permission
    ]


@pytest.mark.django_db
def test_replaces_only_managed_groups_model_permissions(monkeypatch):
    """
    Don't replace permissions that have been added to the model from sources
    other than the model permissions setter command.
    """
    app_label = "leasing"
    model_name = "replacementtestmodel"
    model = make_model(app_label, model_name)
    permissions = create_permissions(app_label, model_name)
    managed_group = Group.objects.create(id=1, name="Managed")
    unmanaged_group = Group.objects.create(id=8, name="Unmanaged")
    unrelated_content_type = ContentType.objects.create(
        app_label=app_label, model="unrelatedmodel"
    )
    unrelated_permission = Permission.objects.create(
        content_type=unrelated_content_type,
        codename="view_unrelatedmodel",
        name="Can view unrelated model",
    )
    managed_group.permissions.add(
        permissions[f"add_{model_name}"], unrelated_permission
    )
    unmanaged_group.permissions.add(permissions[f"add_{model_name}"])

    monkeypatch.setattr(
        set_group_model_permissions,
        "DEFAULT_APP_PERMS",
        {
            app_label: {
                model_name: {set_group_model_permissions.UG.SELAILIJA: ("view",)}
            }
        },
    )
    configure_models(monkeypatch, {app_label: [model]})

    call_command("set_group_model_permissions")

    assert set(managed_group.permissions.values_list("codename", flat=True)) == {
        f"view_{model_name}",
        unrelated_permission.codename,
    }
    assert set(unmanaged_group.permissions.values_list("codename", flat=True)) == {
        f"add_{model_name}"
    }


@pytest.mark.django_db
def test_skips_models_without_default_permissions(monkeypatch):
    app_label = "leasing"
    model_name = "unconfiguredtestmodel"
    model = make_model(app_label, model_name)
    Group.objects.create(id=1, name="Test group")
    monkeypatch.setattr(
        set_group_model_permissions, "DEFAULT_APP_PERMS", {app_label: {}}
    )
    configure_models(monkeypatch, {app_label: [model]})
    stdout = StringIO()

    call_command("set_group_model_permissions", stdout=stdout)

    assert (
        f'Model "{model_name}" not in DEFAULT_APP_PERMS["{app_label}"]. Skipping.'
        in stdout.getvalue()
    )


@pytest.mark.django_db
def test_command_is_repeatable_and_logs_assignments(monkeypatch):
    """Multiple invocations of the command should not duplicate permissions."""
    app_label = "leasing"
    model_name = "repeatabletestmodel"
    model = make_model(app_label, model_name)
    create_permissions(app_label, model_name)
    group = Group.objects.create(id=1, name="Test group")
    monkeypatch.setattr(
        set_group_model_permissions,
        "DEFAULT_APP_PERMS",
        {
            app_label: {
                model_name: {set_group_model_permissions.UG.SELAILIJA: ("view",)}
            }
        },
    )
    configure_models(monkeypatch, {app_label: [model]})
    stdout = StringIO()

    call_command("set_group_model_permissions", stdout=stdout)
    call_command("set_group_model_permissions", stdout=stdout)

    assert (
        stdout.getvalue().count(
            f'Added model permissions for group "{group.name}": view_{model_name}'
        )
        == 2
    )
    assert list(group.permissions.values_list("codename", flat=True)) == [
        f"view_{model_name}"
    ]
