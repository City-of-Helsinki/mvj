from unittest.mock import patch

import pytest
from django.contrib.gis.geos import GEOSGeometry
from django.core.exceptions import BadRequest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from forms.serializers.form import (
    EXCLUDED_ATTACHMENT_FIELDS,
    AttachmentPublicSerializer,
)
from plotsearch.models.plot_search import AreaSearchAttachment, AreaSearchLessor
from plotsearch.serializers.plot_search import (
    EXCLUDED_AREA_SEARCH_ATTACHMENT_FIELDS,
    AreaSearchAttachmentPublicSerializer,
    AreaSearchAttachmentSerializer,
    AreaSearchSerializer,
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
def test_area_search_attachment_amr_with_mock_request(user_factory, rf):
    user = user_factory(email="test@hel.fi")
    example_file = SimpleUploadedFile(name="example.txt", content=b"Lorem lipsum")

    request = rf.post("/")
    request.user = user

    class MockAuth:
        def __init__(self):
            self.data = {"amr": ["helsinkiad", "some-auth-method"]}

    request.auth = MockAuth()

    serializer_context = {"request": request}
    serializer = AreaSearchAttachmentSerializer(
        data={"name": "Test Attachment", "attachment": example_file},
        context=serializer_context,
    )

    assert serializer.is_valid()
    attachment: AreaSearchAttachment = serializer.save()

    assert attachment.user_amr_list == "helsinkiad,some-auth-method"
    assert attachment.is_user_helsinki_ad() is True


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


@pytest.fixture
def areasearch_serializer_with_location() -> AreaSearchSerializer:
    """AreaSearchSerializer with address and district."""
    serializer_with_defaults = AreaSearchSerializer()
    custom_data = serializer_with_defaults.data.copy()
    custom_data.update(
        {
            "address": "Existing address from areasearch",
            "district": "Existing district from areasearch",
        }
    )
    serializer = AreaSearchSerializer(data=custom_data)
    serializer.is_valid()
    return serializer


def test_get_address_and_district_from_geometry(
    areasearch_serializer_with_location: AreaSearchSerializer,
):
    """
    AreaSearchSerializer:
    If geometry data is provided in validated_data, pull address and district
    from there, even if areasearch has an existing address and district.
    """
    address_from_geometry = "New address from geometry"
    district_from_geometry = "New district from geometry"
    dummy_geometry = GEOSGeometry(
        "MULTIPOLYGON (((24.967535 60.174334, 24.966888 60.173293, 24.970275 60.172791, 24.970922 60.17412, 24.967535 60.174334)))"  # noqa: E501
    )
    validated_data = {"geometry": dummy_geometry}

    with patch(
        "plotsearch.serializers.plot_search.AreaSearchSerializer.get_address_and_district_from_kartta_hel"
    ) as mock_kartta_hel:
        mock_kartta_hel.return_value = (address_from_geometry, district_from_geometry)
        address, district = (
            areasearch_serializer_with_location._get_address_and_district(
                validated_data
            )
        )
        assert address == address_from_geometry
        assert district == district_from_geometry


def test_get_address_and_district_from_existing_data(
    areasearch_serializer_with_location: AreaSearchSerializer,
):
    """
    AreaSearchSerializer:
    If geometry data is not provided in validated_data, pull address and district
    from existing areasearch data.
    """
    validated_data = {}
    address, district = areasearch_serializer_with_location._get_address_and_district(
        validated_data
    )
    assert address == areasearch_serializer_with_location.data["address"]
    assert district == areasearch_serializer_with_location.data["district"]


def test_get_address_and_district_from_same_source(
    areasearch_serializer_with_location: AreaSearchSerializer,
):
    """
    AreaSearchSerializer:
    If both
    - geometry query returns a partial result, e.g. only an address or only a district, and
    - areasearch has existing address or district data,

    then only pull both the address and district (or None where present) from geometry query.
    """
    dummy_geometry = GEOSGeometry(
        "MULTIPOLYGON (((24.967535 60.174334, 24.966888 60.173293, 24.970275 60.172791, 24.970922 60.17412, 24.967535 60.174334)))"  # noqa: E501
    )
    validated_data = {"geometry": dummy_geometry}
    address_from_geometry = "New address from geometry"
    with patch(
        "plotsearch.serializers.plot_search.AreaSearchSerializer.get_address_and_district_from_kartta_hel"
    ) as mock_kartta_hel_without_district:
        mock_kartta_hel_without_district.return_value = (address_from_geometry, None)
        address, district = (
            areasearch_serializer_with_location._get_address_and_district(
                validated_data
            )
        )
        assert address == address_from_geometry
        assert district is None

    district_from_geometry = "New district from geometry"
    with patch(
        "plotsearch.serializers.plot_search.AreaSearchSerializer.get_address_and_district_from_kartta_hel"
    ) as mock_kartta_hel_without_address:
        mock_kartta_hel_without_address.return_value = (None, district_from_geometry)
        address, district = (
            areasearch_serializer_with_location._get_address_and_district(
                validated_data
            )
        )
        assert address is None
        assert district == district_from_geometry


def test_get_address_and_district_as_none():
    """
    AreaSearchSerializer:
    If neither geometry data or existing location data exists, return a tuple of Nones.
    """
    areasearch_serializer_without_location = AreaSearchSerializer()
    validated_data = {}
    address, district = (
        areasearch_serializer_without_location._get_address_and_district(validated_data)
    )
    assert address is None
    assert district is None


@pytest.mark.django_db
def test_areasearch_update_email_is_sent(
    setup_lessor_contacts_and_service_units,
    admin_client,
    area_search_test_data,
    area_search_intended_use_factory,
):
    """When areasearch is updated with a new lessor, email is sent to the correct lessor contacts."""
    old_lessor = AreaSearchLessor.MAKE
    new_lessor = AreaSearchLessor.AKV

    name = "Muu alueen käyttö"
    intended_use = area_search_intended_use_factory(name=name, name_fi=name)

    area_search = area_search_test_data
    area_search.lessor = old_lessor
    area_search.intended_use = intended_use
    area_search.save()

    with patch("plotsearch.utils.send_email") as mock_send_email:
        url = reverse("v1:areasearch-detail", kwargs={"pk": area_search_test_data.id})
        response = admin_client.patch(
            url, data={"lessor": new_lessor}, content_type="application/json"
        )

        assert response.status_code == 200
        assert mock_send_email.called
        assert mock_send_email.call_count == 1

        email_input = mock_send_email.call_args[0][0]
        assert email_input.get("from_email")  # from-address is not empty
        assert email_input.get("subject")  # subject is not empty
        assert email_input.get("body")  # body is not empty

        # Emails are sent to two different addresses
        to_addresses = email_input.get("to", [])
        assert len(to_addresses) == 2
        assert to_addresses[0] != to_addresses[1]


@pytest.mark.django_db
def test_areasearch_update_email_is_not_sent(
    setup_lessor_contacts_and_service_units,
    admin_client,
    area_search_test_data,
    area_search_intended_use_factory,
):
    """When areasearch is updated, but lessor field is not changed, no email is sent to lessor contacts."""
    lessor = AreaSearchLessor.MAKE
    name = "Muu alueen käyttö"
    intended_use = area_search_intended_use_factory(name=name, name_fi=name)

    area_search = area_search_test_data
    area_search.lessor = lessor
    area_search.intended_use = intended_use
    area_search.save()

    with patch("plotsearch.utils.send_email") as mock_send_email, patch(
        "plotsearch.utils.send_areasearch_lessor_changed_email"
    ) as mock_generate_email:
        url = reverse("v1:areasearch-detail", kwargs={"pk": area_search_test_data.id})

        # Case 1: lessor is included in data, but same as original
        response = admin_client.patch(
            url, data={"lessor": lessor}, content_type="application/json"
        )
        assert response.status_code == 200
        assert mock_generate_email.called is False
        assert mock_send_email.called is False

        # Case 2: lessor is not included in data
        response = admin_client.patch(url, data={}, content_type="application/json")
        assert response.status_code == 200
        assert mock_generate_email.called is False
        assert mock_send_email.called is False
