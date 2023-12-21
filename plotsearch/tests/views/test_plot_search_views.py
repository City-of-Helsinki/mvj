from dataclasses import dataclass

import pytest
from django.test import override_settings
from rest_framework.serializers import ValidationError

from leasing.models import CustomDetailedPlan, PlanUnit
from plotsearch.views.plot_search import TargetStatusGeneratePDF


def test_get_nested_attr():
    get_nested_attr = TargetStatusGeneratePDF.get_nested_attr

    @dataclass
    class D:
        foo = 1

    @dataclass
    class C:
        d = D()

    @dataclass
    class B:
        c = C()

    @dataclass
    class A:
        b = B()

    @dataclass
    class Empty:
        pass

    a = A()
    assert get_nested_attr(a, "b.c.d.foo") == 1
    assert isinstance(get_nested_attr(a, "b.c"), C)
    assert isinstance(get_nested_attr(a, "b"), B)
    assert get_nested_attr(a, "b.c.d.foo.bar") is None
    assert get_nested_attr(a, "b.c.d.foo.bar.baz", default="lucky") == "lucky"
    empty = Empty()
    assert get_nested_attr(empty, "does_not_exist") is None
    assert get_nested_attr(a, "") is None


@pytest.mark.django_db
def test_target_status_pdf_get_plan(
    target_status_factory, custom_detailed_plan_factory
):
    target_status = target_status_factory()
    view = TargetStatusGeneratePDF()
    plan = view._get_plan(target_status)
    assert plan == target_status.plot_search_target.plan_unit
    assert isinstance(plan, PlanUnit)

    custom_detailed_plan = custom_detailed_plan_factory()
    target_status = target_status_factory(
        plot_search_target__custom_detailed_plan=custom_detailed_plan,
        plot_search_target__plan_unit=None,
    )
    plan = view._get_plan(target_status)
    assert plan == target_status.plot_search_target.custom_detailed_plan
    assert isinstance(plan, CustomDetailedPlan)

    custom_detailed_plan = custom_detailed_plan_factory()
    with pytest.raises(ValidationError):
        target_status = target_status_factory(
            plot_search_target__custom_detailed_plan=custom_detailed_plan,
            # plot_search_target__plan_unit gets generated in the factory
        )

    with pytest.raises(ValidationError):
        target_status = target_status_factory(
            plot_search_target__custom_detailed_plan=None,
            plot_search_target__plan_unit=None,
        )


@pytest.mark.django_db
def test_target_status_pdf_get_plan_intended_use(
    target_status_factory, custom_detailed_plan_factory
):
    view = TargetStatusGeneratePDF()
    target_status = target_status_factory()
    assert (
        view._get_plan_intended_use(target_status)
        == target_status.plot_search_target.plan_unit.plan_unit_intended_use
    )

    custom_detailed_plan = custom_detailed_plan_factory()
    target_status = target_status_factory(
        plot_search_target__custom_detailed_plan=custom_detailed_plan,
        plot_search_target__plan_unit=None,
    )
    assert (
        view._get_plan_intended_use(target_status)
        == target_status.plot_search_target.custom_detailed_plan.intended_use
    )


@pytest.mark.django_db
@override_settings(LANGUAGE_CODE="en")
def test_target_status_pdf_get_plot_search_information(target_status_factory):
    target_status = target_status_factory(
        plot_search_target__plan_unit__area=21345,
        plot_search_target__plot_search__end_at=None,
    )
    view = TargetStatusGeneratePDF()
    plot_search_information = view._get_plot_search_information(target_status)
    labels = {}
    for x in plot_search_information:
        labels[x["label"]] = x["value"]
    assert labels["Plot"].startswith("91-1-30-")
    assert labels["Intended use"] == ""
    assert labels["Area (m²)"] == 21345
    assert (
        "The deadline for applications" not in labels.keys()
    ), "This key should not be here since it was set None"
