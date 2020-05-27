import pytest

from field_permissions.tests.dummy_app.models import Dummy


@pytest.mark.django_db
def test_in_registry():
    from field_permissions.registry import FieldPermissionsModelRegistry

    field_permissions = FieldPermissionsModelRegistry()
    field_permissions.register(Dummy)

    tm = Dummy.objects.create(field1="test")
    assert field_permissions.in_registry(tm)


@pytest.mark.django_db
def test_not_in_registry():
    from field_permissions.registry import FieldPermissionsModelRegistry

    field_permissions = FieldPermissionsModelRegistry()

    assert not field_permissions.in_registry(Dummy)


@pytest.mark.django_db
def test_get_model_fields_all_fields():
    from field_permissions.registry import FieldPermissionsModelRegistry

    field_permissions = FieldPermissionsModelRegistry()
    field_permissions.register(Dummy)

    model_field_names = [
        field.name for field in field_permissions.get_model_fields(Dummy)
    ]
    assert model_field_names == [
        "dummysub",
        "id",
        "field1",
        "field2",
        "field3",
        "second_sub",
    ]


@pytest.mark.django_db
def test_get_model_fields_include_some_fields():
    from field_permissions.registry import FieldPermissionsModelRegistry

    field_permissions = FieldPermissionsModelRegistry()
    field_permissions.register(Dummy, include_fields=["id", "field1"])

    model_field_names = [
        field.name for field in field_permissions.get_model_fields(Dummy)
    ]
    assert model_field_names == ["id", "field1"]


@pytest.mark.django_db
def test_get_model_fields_exclude_some_fields():
    from field_permissions.registry import FieldPermissionsModelRegistry

    field_permissions = FieldPermissionsModelRegistry()
    field_permissions.register(Dummy, exclude_fields=["field1", "dummysub"])

    model_field_names = [
        field.name for field in field_permissions.get_model_fields(Dummy)
    ]
    assert model_field_names == ["id", "field2", "field3", "second_sub"]


@pytest.mark.django_db
def test_get_field_permissions_for_model():
    from field_permissions.registry import FieldPermissionsModelRegistry

    field_permissions = FieldPermissionsModelRegistry()
    field_permissions.register(Dummy)

    perms = field_permissions.get_field_permissions_for_model(Dummy)
    perm_codenames = [codename for (codename, name) in perms]

    assert perm_codenames == [
        "view_dummy_dummysub_set",
        "change_dummy_dummysub_set",
        "view_dummy_id",
        "change_dummy_id",
        "view_dummy_field1",
        "change_dummy_field1",
        "view_dummy_field2",
        "change_dummy_field2",
        "view_dummy_field3",
        "change_dummy_field3",
        "view_dummy_second_sub",
        "change_dummy_second_sub",
    ]
