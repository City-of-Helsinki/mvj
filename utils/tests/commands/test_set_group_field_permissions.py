from io import StringIO
from types import SimpleNamespace

import pytest
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management import call_command

from utils.group_permissions import UG
from utils.management.commands import set_group_field_permissions


def make_model(model_name):
    return type(
        model_name.title(), (), {"_meta": SimpleNamespace(model_name=model_name)}
    )


def create_field_permissions(model_name, field_names):
    content_type = ContentType.objects.create(
        app_label="leasing", model=f"fieldpermission{model_name}"
    )
    for field_name in field_names:
        for permission_type in ("view", "change"):
            Permission.objects.create(
                content_type=content_type,
                codename=f"{permission_type}_{model_name}_{field_name}",
                name=f"Can {permission_type} {field_name}",
            )


@pytest.mark.django_db
def test_applies_field_defaults_and_overrides_repeatably(monkeypatch):
    model_name = "fieldpermissiontest"
    model = make_model(model_name)
    create_field_permissions(model_name, ("title", "secret"))
    viewer = Group.objects.create(id=UG.SELAILIJA, name="Viewer")
    preparer = Group.objects.create(id=UG.VALMISTELIJA, name="Preparer")
    monkeypatch.setattr(
        set_group_field_permissions,
        "FIELD_PERMISSION_CONFIGS",
        (
            {
                model: {
                    "model": {},
                    "fields": {
                        "_default": {
                            UG.SELAILIJA: "view",
                            UG.VALMISTELIJA: "change",
                        },
                        "secret": {UG.SELAILIJA: None},
                    },
                }
            },
        ),
    )
    from field_permissions.registry import field_permissions

    monkeypatch.setattr(field_permissions, "get_models", lambda: [model])
    monkeypatch.setattr(
        field_permissions,
        "get_field_permissions_for_model",
        lambda _model: [
            (f"view_{model_name}_title", ""),
            (f"change_{model_name}_title", ""),
            (f"view_{model_name}_secret", ""),
            (f"change_{model_name}_secret", ""),
        ],
    )

    stdout = StringIO()
    call_command("set_group_field_permissions", stdout=stdout)
    call_command("set_group_field_permissions", stdout=stdout)

    assert set(viewer.permissions.values_list("codename", flat=True)) == {
        f"view_{model_name}_title"
    }
    assert set(preparer.permissions.values_list("codename", flat=True)) == {
        f"change_{model_name}_title",
        f"change_{model_name}_secret",
    }
    assert stdout.getvalue().count("Added field permissions") == 4
