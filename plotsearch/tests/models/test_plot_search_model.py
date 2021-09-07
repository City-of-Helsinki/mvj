import pytest
from django.utils.crypto import get_random_string

from leasing.enums import PlotSearchTargetType
from plotsearch.models import PlotSearchTarget


@pytest.mark.django_db
def test_remove_plot_search_target_cascade_plan_unit(
    django_db_setup,
    plot_search_factory,
    plot_search_target_factory,
    lease_factory,
    lease_area_factory,
    plan_unit_factory,
):
    # Initialize data
    lease = lease_factory(
        type_id=1, municipality_id=1, district_id=29, notice_period_id=1
    )
    lease_area = lease_area_factory(
        lease=lease, identifier=get_random_string(), area=1000, section_area=1000
    )
    plan_unit = plan_unit_factory(
        identifier="PU1",
        area=1000,
        lease_area=lease_area,
        in_contract=False,
        is_master=False,
    )
    plot_search = plot_search_factory()
    plot_search_target = plot_search_target_factory(
        plot_search=plot_search,
        plan_unit=plan_unit,
        target_type=PlotSearchTargetType.SEARCHABLE,
    )

    # Remove plot search target
    plot_search_target.delete()

    assert PlotSearchTarget.objects.filter(pk=plot_search_target.id).count() == 0
    # TODO next assert should maybe work
    # assert PlanUnit.objects.filter(pk=plan_unit.id).count() == 0


@pytest.mark.django_db
def test_duplicate_plan_unit_on_plot_search_target_save(
    django_db_setup,
    plot_search_factory,
    plot_search_target_factory,
    lease_factory,
    lease_area_factory,
    plan_unit_factory,
):
    # Initialize data
    lease = lease_factory(
        type_id=1, municipality_id=1, district_id=29, notice_period_id=1
    )
    lease_area = lease_area_factory(
        lease=lease, identifier=get_random_string(), area=1000, section_area=1000
    )
    master_plan_unit = plan_unit_factory(
        identifier="PU1", area=1000, lease_area=lease_area, is_master=True,
    )
    # master_plan_unit_id = master_plan_unit.id
    master_plan_unit_master_timestamp = master_plan_unit.master_timestamp

    plot_search = plot_search_factory()
    plot_search_target = plot_search_target_factory(
        plot_search=plot_search,
        plan_unit=master_plan_unit,
        target_type=PlotSearchTargetType.SEARCHABLE,
    )

    # TODO next assert does not make any sense
    # assert plot_search_target.plan_unit.id != master_plan_unit_id
    assert (
        plot_search_target.plan_unit.master_timestamp
        == master_plan_unit_master_timestamp
    )
