import pytest
from django.core.exceptions import BadRequest
from django.core.files.uploadedfile import SimpleUploadedFile

from forms.serializers.form import (
    EXCLUDED_ATTACHMENT_FIELDS,
    AttachmentPublicSerializer,
)
from plotsearch.serializers.plot_search import (
    EXCLUDED_AREA_SEARCH_ATTACHMENT_FIELDS,
    AreaSearchAttachmentPublicSerializer,
    PlotSearchTargetCreateUpdateSerializer,
)


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


@pytest.mark.django_db
def test_attachment_public_serializer_unwanted_fields(attachment_factory, user_factory):
    user = user_factory()
    example_file = SimpleUploadedFile(name="example.txt", content=b"Lorem lipsum")
    attachment = attachment_factory(attachment=example_file, user=user)
    data = AttachmentPublicSerializer(attachment).data
    unwanted_fields_in_data = set(data.keys()).intersection(
        set(EXCLUDED_ATTACHMENT_FIELDS)
    )
    assert len(unwanted_fields_in_data) == 0


@pytest.mark.django_db
def test_area_search_attachment_public_serializer_unwanted_fields(
    area_search_attachment_factory, user_factory
):
    user = user_factory()
    example_file = SimpleUploadedFile(name="example.txt", content=b"Lorem lipsum")
    area_search_attachment = area_search_attachment_factory(
        attachment=example_file, user=user
    )
    data = AreaSearchAttachmentPublicSerializer(area_search_attachment).data
    unwanted_fields_in_data = set(data.keys()).intersection(
        set(EXCLUDED_AREA_SEARCH_ATTACHMENT_FIELDS)
    )
    assert len(unwanted_fields_in_data) == 0
