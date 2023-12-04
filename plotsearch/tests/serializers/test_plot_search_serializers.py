import pytest
from django.core.exceptions import BadRequest

from plotsearch.serializers.plot_search import PlotSearchTargetCreateUpdateSerializer


@pytest.mark.django_db
def test_get_plan_unit_or_custom_detailed_plan_with_plan_unit(plan_unit_factory):
    serializer = PlotSearchTargetCreateUpdateSerializer()
    plan_unit = plan_unit_factory()
    validated_data = {"plan_unit_id": plan_unit.id}

    (
        custom_detailed_plan,
        result_plan_unit,
    ) = serializer.get_plan_unit_or_custom_detailed_plan(validated_data)

    assert custom_detailed_plan is None
    assert result_plan_unit == plan_unit


@pytest.mark.django_db
def test_get_plan_unit_or_custom_detailed_plan_with_custom_detailed_plan(
    custom_detailed_plan_factory,
):
    serializer = PlotSearchTargetCreateUpdateSerializer()
    custom_detailed_plan = custom_detailed_plan_factory()
    validated_data = {"custom_detailed_plan_id": custom_detailed_plan.id}

    (
        result_custom_detailed_plan,
        plan_unit,
    ) = serializer.get_plan_unit_or_custom_detailed_plan(validated_data)

    assert result_custom_detailed_plan == custom_detailed_plan
    assert plan_unit is None


@pytest.mark.django_db
def test_get_plan_unit_or_custom_detailed_plan_badrequest(
    plan_unit_factory, custom_detailed_plan_factory
):
    serializer = PlotSearchTargetCreateUpdateSerializer()

    # Case 1: Both plan_unit_id and custom_detailed_plan_id supplied
    plan_unit = plan_unit_factory()
    custom_detailed_plan = custom_detailed_plan_factory()
    validated_data = {
        "plan_unit_id": plan_unit.id,
        "custom_detailed_plan_id": custom_detailed_plan.id,
    }
    with pytest.raises(BadRequest):
        serializer.get_plan_unit_or_custom_detailed_plan(validated_data)

    # Case 2: Invalid plan_unit is supplied
    invalid_plan_unit_id = 9999
    validated_data = {"plan_unit_id": invalid_plan_unit_id}
    with pytest.raises(BadRequest):
        serializer.get_plan_unit_or_custom_detailed_plan(validated_data)

    # Case 3: Invalid custom_detailed_plan is supplied
    invalid_custom_detailed_plan_id = 9999
    validated_data = {"custom_detailed_plan_id": invalid_custom_detailed_plan_id}
    with pytest.raises(BadRequest):
        serializer.get_plan_unit_or_custom_detailed_plan(validated_data)

    # Case 4: Neither plan_unit_id nor custom_detailed_plan_id is supplied
    validated_data = {}
    with pytest.raises(BadRequest):
        serializer.get_plan_unit_or_custom_detailed_plan(validated_data)
