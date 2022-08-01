import pytest


@pytest.mark.django_db
def test_adding_new_service_unit(
    user, group, service_unit, service_unit_group_mapping_factory
):
    assert user.service_units.count() == 0
    service_unit_group_mapping_factory(group=group, service_unit=service_unit)
    user.groups.add(group)

    user.update_service_units()

    assert user.service_units.count() == 1


@pytest.mark.django_db
def test_removing_service_unit(
    user, group, service_unit, service_unit_group_mapping_factory
):
    service_unit_group_mapping_factory(group=group, service_unit=service_unit)
    user.service_units.add(service_unit)

    user.update_service_units()

    assert user.service_units.count() == 0


@pytest.mark.django_db
def test_non_managed_service_unit_is_not_removed(user, service_unit):
    user.service_units.add(service_unit)

    user.update_service_units()

    assert user.service_units.count() == 1


@pytest.mark.django_db
def test_existing_service_units_are_kept(
    user, group, service_unit_factory, service_unit_group_mapping_factory
):
    service_unit1 = service_unit_factory()
    service_unit2 = service_unit_factory()
    service_unit_group_mapping_factory(group=group, service_unit=service_unit1)
    service_unit_group_mapping_factory(group=group, service_unit=service_unit2)
    user.groups.add(group)
    user.service_units.add(service_unit1)
    user.service_units.add(service_unit2)

    user.update_service_units()

    assert user.service_units.count() == 2


@pytest.mark.django_db
def test_new_are_added_and_excess_are_removed(
    user, group_factory, service_unit_factory, service_unit_group_mapping_factory
):
    service_unit1 = service_unit_factory()
    group1 = group_factory(name="G1")
    service_unit2 = service_unit_factory()
    group2 = group_factory(name="G2")
    service_unit3 = service_unit_factory()
    group3 = group_factory(name="G3")
    service_unit_group_mapping_factory(group=group1, service_unit=service_unit1)
    service_unit_group_mapping_factory(group=group2, service_unit=service_unit2)
    service_unit_group_mapping_factory(group=group3, service_unit=service_unit3)
    user.groups.add(group2)
    user.groups.add(group3)
    user.service_units.add(service_unit1)
    user.service_units.add(service_unit2)

    user.update_service_units()

    assert set(user.service_units.all()) == {service_unit2, service_unit3}
