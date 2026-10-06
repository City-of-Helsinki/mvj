from io import StringIO
from typing import Callable

import pytest
from django.core.management import call_command

from leasing.enums import PlanUnitStatus, PlotType
from leasing.models import LeaseArea, PlanUnit, Plot
from leasing.models.area import Area
from leasing.models.lease import Lease


@pytest.mark.django_db
def test_attach_areas_to_lease_areas(
    lease_area_factory: Callable[..., LeaseArea],
    plan_unit_factory: Callable[..., PlanUnit],
    plot_factory: Callable[..., Plot],
    area_with_intersects_test_data,
    lease_test_data,
):
    """Imported spatial data replaces stale derived data, not contract data."""

    area: Area = area_with_intersects_test_data["area"]
    intersect_areas: list[Area] = area_with_intersects_test_data["intersect_areas"]

    real_property_area = next(
        intersect_area
        for intersect_area in intersect_areas
        if intersect_area.external_id == "13985"
    )

    plan_unit_area = next(
        intersect_area
        for intersect_area in intersect_areas
        if intersect_area.external_id == "23061"
    )

    plot_division_area = next(
        intersect_area
        for intersect_area in intersect_areas
        if intersect_area.external_id == "1974"
    )

    lease: Lease = lease_test_data["lease"]

    lease_area = lease_area_factory(
        lease=lease,
        identifier=area.get_land_identifier(),
        area=1000,
        section_area=1000,
    )

    contract_plan_unit = plan_unit_factory(
        identifier="PU1", area=1000, lease_area=lease_area, in_contract=True
    )

    extra_plot = plot_factory(
        identifier="PLOT_EXTRA",
        area=1000,
        type=PlotType.REAL_PROPERTY,
        lease_area=lease_area,
    )
    extra_plan_unit = plan_unit_factory(
        identifier="PLAN_UNIT_EXTRA", area=1000, lease_area=lease_area
    )

    call_command("attach_areas", stdout=StringIO())

    lease_area = LeaseArea.objects.get(identifier=area.get_land_identifier())
    assert area.geometry == lease_area.geometry

    # Intersecting real property data becomes the lease area's derived plot.
    derived_plots = Plot.objects.filter(lease_area=lease_area, in_contract=False)
    assert derived_plots.count() == 1
    plot = derived_plots.get()
    assert plot.identifier == real_property_area.get_denormalized_identifier()
    assert plot.type == PlotType[real_property_area.type.value.upper()]
    assert plot.is_master is True
    assert plot.area == int(float(real_property_area.metadata["area"]))
    assert plot.section_area > 0
    assert plot.geometry == real_property_area.geometry
    assert (
        plot.registration_date.isoformat()
        == real_property_area.metadata["registration_date"]
    )
    assert plot.repeal_date == real_property_area.metadata["repeal_date"]

    # Plan units also carry domain data from their related plot division and plan.
    derived_plan_units = PlanUnit.objects.filter(
        lease_area=lease_area, in_contract=False
    )
    assert derived_plan_units.count() == 1
    plan_unit = derived_plan_units.get()
    assert plan_unit.identifier == plan_unit_area.get_denormalized_identifier()
    assert plan_unit.is_master is True
    assert plan_unit.area == int(float(plan_unit_area.metadata["area"]))
    assert plan_unit.section_area > 0
    assert plan_unit.geometry == plan_unit_area.geometry
    assert plan_unit.plot_division_identifier == plot_division_area.identifier
    assert (
        plan_unit.plot_division_date_of_approval.isoformat()
        == plot_division_area.metadata["date_of_approval"]
    )
    assert (
        plan_unit.plot_division_effective_date
        == plot_division_area.metadata["effective_date"]
    )
    assert (
        plan_unit.plot_division_state.name == plot_division_area.metadata["state_name"]
    )
    assert (
        plan_unit.detailed_plan_identifier
        == plan_unit_area.metadata["detailed_plan_identifier"]
    )
    assert plan_unit.plan_unit_type.name == plan_unit_area.metadata["type_name"]
    assert plan_unit.plan_unit_state.name == plan_unit_area.metadata["state_name"]
    assert plan_unit.plan_unit_status == PlanUnitStatus.PRESENT
    assert (
        plan_unit.plan_unit_intended_use.name
        == plan_unit_area.metadata["intended_use_name"]
    )

    # Contract data is authoritative; only stale derived records are removed.
    assert PlanUnit.objects.filter(pk=contract_plan_unit.pk, in_contract=True).exists()
    assert not Plot.objects.filter(pk=extra_plot.pk).exists()
    assert not PlanUnit.objects.filter(pk=extra_plan_unit.pk).exists()


@pytest.mark.django_db
def test_attach_areas_preserves_contract_items(
    lease_area_factory: Callable[..., LeaseArea],
    plan_unit_factory: Callable[..., PlanUnit],
    plot_factory: Callable[..., Plot],
    area_with_intersects_test_data,
    lease_test_data,
):
    """Imported data must not remove plots or plan units recorded in a contract."""
    lease: Lease = lease_test_data["lease"]
    area: Area = area_with_intersects_test_data["area"]
    lease_area = lease_area_factory(
        lease=lease,
        identifier=area.get_land_identifier(),
        area=1000,
        section_area=1000,
    )
    contract_plot = plot_factory(
        identifier="PLOT_IN_CONTRACT",
        area=1000,
        type=PlotType.REAL_PROPERTY,
        lease_area=lease_area,
        in_contract=True,
    )
    contract_plan_unit = plan_unit_factory(
        identifier="PLAN_UNIT_IN_CONTRACT",
        area=1000,
        lease_area=lease_area,
        in_contract=True,
    )

    call_command("attach_areas", stdout=StringIO())

    assert Plot.objects.filter(pk=contract_plot.pk).exists()
    assert PlanUnit.objects.filter(pk=contract_plan_unit.pk).exists()


@pytest.mark.django_db
def test_attach_areas_ignores_candidates_without_area_metadata(
    lease_area_factory: Callable[..., LeaseArea],
    area_with_intersects_test_data,
    lease_test_data,
):
    """Test a case from 2020: sometimes the source DB has misformed area records
    without area metadata. We don't want to import these"""
    lease: Lease = lease_test_data["lease"]
    area: Area = area_with_intersects_test_data["area"]
    lease_area = lease_area_factory(
        lease=lease,
        identifier=area.get_land_identifier(),
        area=1000,
        section_area=1000,
    )
    area_without_area_metadata = next(
        intersect_area
        for intersect_area in area_with_intersects_test_data["intersect_areas"]
        if intersect_area.metadata.get("area") is None
    )
    ignored_plot_identifier = area_without_area_metadata.get_denormalized_identifier()

    call_command("attach_areas", stdout=StringIO())

    assert not lease_area.plots.filter(identifier=ignored_plot_identifier).exists()


@pytest.mark.django_db
def test_attach_areas_reuses_derived_records_on_repeated_run(
    lease_area_factory: Callable[..., LeaseArea],
    area_with_intersects_test_data,
    lease_test_data,
):
    """No new plots or plan units should be created on repeated runs."""
    lease: Lease = lease_test_data["lease"]
    area: Area = area_with_intersects_test_data["area"]
    lease_area = lease_area_factory(
        lease=lease,
        identifier=area.get_land_identifier(),
        area=1000,
        section_area=1000,
    )

    call_command("attach_areas", stdout=StringIO())
    plot_id = lease_area.plots.get(in_contract=False).pk
    plan_unit_id = lease_area.plan_units.get(in_contract=False).pk

    call_command("attach_areas", stdout=StringIO())

    assert list(
        lease_area.plots.filter(in_contract=False).values_list("pk", flat=True)
    ) == [plot_id]
    assert list(
        lease_area.plan_units.filter(in_contract=False).values_list("pk", flat=True)
    ) == [plan_unit_id]


@pytest.mark.django_db
def test_attach_areas_leaves_lease_area_without_imported_area_unchanged(
    plot_factory: Callable[..., Plot],
    lease_test_data,
):
    """A lease area outside the import has no authoritative replacement data."""
    lease_area: LeaseArea = lease_test_data["lease_area"]
    existing_plot = plot_factory(
        identifier="EXISTING_PLOT",
        area=1000,
        type=PlotType.REAL_PROPERTY,
        lease_area=lease_area,
    )

    call_command("attach_areas", stdout=StringIO())

    lease_area.refresh_from_db()
    assert lease_area.geometry is None
    assert Plot.objects.filter(pk=existing_plot.pk).exists()


@pytest.mark.django_db
def test_plan_unit_timestamps_change_only_when_imported_data_changes(
    lease_area_factory: Callable[..., LeaseArea],
    plan_unit_factory: Callable[..., PlanUnit],
    area_with_intersects_test_data,
    lease_test_data,
    monkeypatch,
):
    """A no-op import must not make a plan unit appear newly synchronized."""

    lease: Lease = lease_test_data["lease"]
    area: Area = area_with_intersects_test_data["area"]
    imported_plan_unit_area = next(
        intersect_area
        for intersect_area in area_with_intersects_test_data["intersect_areas"]
        if intersect_area.metadata.get("plan_unit_identifier")
    )
    imported_plan_unit_identifier = (
        imported_plan_unit_area.get_denormalized_identifier()
    )

    lease_area = lease_area_factory(
        lease=lease,
        identifier=area.get_land_identifier(),
        area=1000,
        section_area=1000,
    )

    plan_unit = plan_unit_factory(
        area=1000,
        identifier=imported_plan_unit_identifier,
        in_contract=False,
        lease_area=lease_area,
        is_master=True,
    )

    call_command("attach_areas", stdout=StringIO())

    result_plan_unit = lease_area.plan_units.get(id=plan_unit.id)
    assert result_plan_unit.modified_at > plan_unit.modified_at

    plan_unit.refresh_from_db()

    monkeypatch.setattr(
        "leasing.models.PlanUnit.tracker.tracker_class.changed", lambda x: {}
    )

    call_command("attach_areas", stdout=StringIO())

    result_plan_unit = lease_area.plan_units.get(id=plan_unit.id)
    assert result_plan_unit.master_timestamp == plan_unit.master_timestamp
