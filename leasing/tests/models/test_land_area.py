import pytest


@pytest.mark.django_db
def test_plan_unit_cannot_create_another_master_plan_unit(
    lease_test_data, plan_unit_factory
):
    master_plan_unit = plan_unit_factory(
        area=100,
        lease_area=lease_test_data["lease_area"],
        identifier="1234",
        is_master=True,
    )

    another_master_plan_unit = master_plan_unit
    another_master_plan_unit.pk = None

    with pytest.raises(Exception):
        another_master_plan_unit.save()
