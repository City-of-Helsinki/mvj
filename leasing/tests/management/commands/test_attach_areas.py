from io import StringIO

import pytest
from django.core.management import call_command

from leasing.enums import PlotType
from leasing.models import LeaseArea, PlanUnit, Plot


@pytest.mark.django_db
def test_attach_areas_to_lease_areas(
    lease_area_factory,
    plan_unit_factory,
    plot_factory,
    area_with_intersects_test_data,
    lease_test_data,
):
    out = StringIO()
    args = []
    opts = {}

    area = area_with_intersects_test_data["area"]
    lease = lease_test_data["lease"]

    # Add lease area to lease
    lease_area = lease_area_factory(
        lease=lease,
        identifier=area_with_intersects_test_data["area"].get_land_identifier(),
        area=1000,
        section_area=1000,
    )

    # Add plan unit to contract
    plan_unit_factory(
        identifier="PU1", area=1000, lease_area=lease_area, in_contract=True
    )

    # Extra plot and plan unit which are not in contracts
    extra_plot = plot_factory(
        identifier="PLOT_EXTRA",
        area=1000,
        type=PlotType.REAL_PROPERTY,
        lease_area=lease_area,
    )
    extra_plan_unit = plan_unit_factory(
        identifier="PLAN_UNIT_EXTRA", area=1000, lease_area=lease_area
    )

    # Geometry data is empty
    assert lease_area.geometry is None

    # Execute command for test
    call_command("attach_areas", stdout=out, *args, **opts)

    # The geometry data has updated for exist lease area
    lease_area = LeaseArea.objects.get(identifier=area.get_land_identifier())
    assert area.geometry == lease_area.geometry

    # Plot saved
    assert lease_area.plots.filter(in_contract=False).count() == 1

    # Plan unit saved
    assert lease_area.plan_units.filter(in_contract=False).count() == 1

    # Extra items has been deleted
    assert not Plot.objects.filter(pk=extra_plot.pk).exists()
    assert not PlanUnit.objects.filter(pk=extra_plan_unit.pk).exists()


@pytest.mark.django_db
def test_plan_unit_updates_modified_at(
    lease_area_factory,
    plan_unit_factory,
    area_with_intersects_test_data,
    lease_test_data,
    monkeypatch,
):
    out = StringIO()
    args = []
    opts = {}

    lease = lease_test_data["lease"]

    lease_area = lease_area_factory(
        lease=lease,
        identifier=area_with_intersects_test_data["area"].get_land_identifier(),
        area=1000,
        section_area=1000,
    )

    plan_unit = plan_unit_factory(
        area=1000,
        identifier="91-28-239-3",
        in_contract=False,
        lease_area=lease_area,
        is_master=True,
    )

    # The field modified_at changes on update
    call_command("attach_areas", stdout=out, *args, **opts)

    result_plan_unit = lease_area.plan_units.get(id=plan_unit.id)
    assert result_plan_unit.modified_at > plan_unit.modified_at

    # The field modified_at not changes on update if there isn't changes
    plan_unit.refresh_from_db()

    monkeypatch.setattr(
        "leasing.models.PlanUnit.tracker.tracker_class.changed", lambda x: {}
    )

    call_command("attach_areas", stdout=out, *args, **opts)

    result_plan_unit = lease_area.plan_units.get(id=plan_unit.id)
    assert result_plan_unit.master_timestamp == plan_unit.master_timestamp
