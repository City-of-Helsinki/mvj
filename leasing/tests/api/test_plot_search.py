import json

import pytest
from django.core.serializers.json import DjangoJSONEncoder
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import get_random_string
from rest_framework import serializers

from leasing.enums import PlotSearchTargetType
from leasing.models import PlanUnit, PlotSearchTarget


@pytest.mark.django_db
def test_plot_search_detail(
    django_db_setup,
    admin_client,
    plan_unit_factory,
    plot_search_test_data,
    lease_test_data,
):
    # Attach plan unit for plot search
    plan_unit = plan_unit_factory(
        identifier="PU1",
        area=1000,
        lease_area=lease_test_data["lease_area"],
        is_master=True,
    )
    PlotSearchTarget.objects.create(
        plot_search=plot_search_test_data, plan_unit=plan_unit
    )

    url = reverse("plotsearch-detail", kwargs={"pk": plot_search_test_data.id})

    response = admin_client.get(url, content_type="application/json")
    assert response.status_code == 200, "%s %s" % (response.status_code, response.data)


@pytest.mark.django_db
def test_plot_search_list(django_db_setup, admin_client, plot_search_test_data):

    url = reverse("plotsearch-list")

    response = admin_client.get(url, content_type="application/json")
    assert response.status_code == 200, "%s %s" % (response.status_code, response.data)


@pytest.mark.django_db
def test_plot_search_create_simple(
    django_db_setup, admin_client, plot_search_test_data, lease_test_data,
):
    url = reverse("plotsearch-list")  # list == create

    data = {
        "name": get_random_string(),
    }

    response = admin_client.post(
        url, json.dumps(data, cls=DjangoJSONEncoder), content_type="application/json"
    )
    assert response.status_code == 201, "%s %s" % (response.status_code, response.data)


@pytest.mark.django_db
def test_plot_search_create(
    django_db_setup,
    admin_client,
    plot_search_test_data,
    lease_test_data,
    user_factory,
    plan_unit_factory,
):
    url = reverse("plotsearch-list")  # list == create

    # Add preparer
    user = user_factory(username="test_user")

    # Add master plan unit
    plan_unit = plan_unit_factory(
        identifier="PU1",
        area=1000,
        lease_area=lease_test_data["lease_area"],
        is_master=True,
    )

    data = {
        "name": get_random_string(),
        "subtype": plot_search_test_data.subtype.id,
        "stage": plot_search_test_data.stage.id,
        "preparer": user.id,
        "begin_at": timezone.now(),
        "end_at": timezone.now() + timezone.timedelta(days=7),
        "targets": [
            {
                "plan_unit": plan_unit.id,
                "target_type": PlotSearchTargetType.SEARCHABLE.value,
            },
        ],
    }

    response = admin_client.post(
        url, json.dumps(data, cls=DjangoJSONEncoder), content_type="application/json"
    )
    assert response.status_code == 201, "%s %s" % (response.status_code, response.data)
    assert response.data["type"]
    assert len(response.data["targets"]) > 0


@pytest.mark.django_db
def test_plot_search_update(
    django_db_setup,
    admin_client,
    plot_search_test_data,
    lease_test_data,
    user_factory,
    plan_unit_factory,
):
    url = reverse(
        "plotsearch-detail", kwargs={"pk": plot_search_test_data.id}
    )  # detail == update

    # Add preparer
    user = user_factory(username="test_user")

    # Add master plan unit
    plan_unit = plan_unit_factory(
        identifier="PU1",
        area=1000,
        lease_area=lease_test_data["lease_area"],
        is_master=True,
    )

    updated_end_at = plot_search_test_data.end_at + timezone.timedelta(days=30)

    data = {
        "name": get_random_string(),
        "subtype": plot_search_test_data.subtype.id,
        "stage": plot_search_test_data.stage.id,
        "preparer": user.id,
        "begin_at": plot_search_test_data.begin_at,
        "end_at": updated_end_at,
        "targets": [
            {
                "plan_unit": plan_unit.id,
                "target_type": PlotSearchTargetType.SEARCHABLE.value,
            },
        ],
    }

    response = admin_client.put(url, data=data, content_type="application/json")
    assert response.status_code == 200, "%s %s" % (response.status_code, response.data)
    assert response.data["end_at"] == serializers.DateTimeField().to_representation(
        updated_end_at
    )
    assert response.data["type"]
    assert len(response.data["targets"]) > 0


@pytest.mark.django_db
def test_plot_search_master_plan_unit_is_deleted(
    django_db_setup,
    admin_client,
    plot_search_test_data,
    lease_test_data,
    plan_unit_factory,
):
    # Attach master plan unit for plot search
    plan_unit = plan_unit_factory(
        identifier="PU1",
        area=1000,
        lease_area=lease_test_data["lease_area"],
        is_master=True,
    )
    master_plan_unit_id = plan_unit.id
    PlotSearchTarget.objects.create(
        plot_search=plot_search_test_data, plan_unit=plan_unit
    )

    # Delete master plan unit
    PlanUnit.objects.get(pk=master_plan_unit_id).delete()

    url = reverse("plotsearch-detail", kwargs={"pk": plot_search_test_data.id})
    response = admin_client.get(url, content_type="application/json")
    assert response.status_code == 200, "%s %s" % (response.status_code, response.data)
    assert not response.data["targets"][0]["master_plan_unit_id"]
    assert response.data["targets"][0]["is_master_plan_unit_deleted"]
    assert len(response.data["targets"][0]["message_label"]) > 0


@pytest.mark.django_db
def test_plot_search_master_plan_unit_is_newer(
    django_db_setup,
    admin_client,
    plot_search_test_data,
    lease_test_data,
    plan_unit_factory,
):
    # Attach master plan unit for plot search
    plan_unit = plan_unit_factory(
        identifier="PU1",
        area=1000,
        lease_area=lease_test_data["lease_area"],
        is_master=True,
    )
    master_plan_unit_id = plan_unit.id
    PlotSearchTarget.objects.create(
        plot_search=plot_search_test_data, plan_unit=plan_unit
    )

    # Update master plan unit
    master_plan_unit = PlanUnit.objects.get(pk=master_plan_unit_id)
    master_plan_unit.detailed_plan_identifier = "DP1"
    master_plan_unit.save()

    url = reverse("plotsearch-detail", kwargs={"pk": plot_search_test_data.id})
    response = admin_client.get(url, content_type="application/json")
    assert response.status_code == 200, "%s %s" % (response.status_code, response.data)
    assert response.data["targets"][0]["master_plan_unit_id"] > 0
    assert response.data["targets"][0]["is_master_plan_unit_newer"]
    assert len(response.data["targets"][0]["message_label"]) > 0


@pytest.mark.django_db
def test_plot_search_master_plan_unit_is_deleted_change_to_new(
    django_db_setup,
    admin_client,
    plot_search_test_data,
    lease_test_data,
    plan_unit_factory,
):
    # Create master plan unit
    plan_unit = plan_unit_factory(
        identifier="PU1",
        area=1000,
        lease_area=lease_test_data["lease_area"],
        is_master=True,
    )
    master_plan_unit_id = plan_unit.id

    # Create second master plan unit
    plan_unit2 = plan_unit_factory(
        identifier="PU2",
        area=1000,
        lease_area=lease_test_data["lease_area"],
        is_master=True,
    )

    # Create plot search target, master plan unit will be duplicated on this
    PlotSearchTarget.objects.create(
        plot_search=plot_search_test_data, plan_unit=plan_unit
    )
    duplicated_plan_unit_id = plan_unit.id

    # Delete master plan unit which has duplicated to plot search target
    PlanUnit.objects.get(pk=master_plan_unit_id).delete()

    # Get plot search detail
    url = reverse("plotsearch-detail", kwargs={"pk": plot_search_test_data.id})
    response = admin_client.get(url, content_type="application/json")
    assert response.status_code == 200, "%s %s" % (response.status_code, response.data)

    # Confirm that the master plan unit has deleted
    assert response.data["targets"][0]["is_master_plan_unit_deleted"]

    # Change to new plan unit
    url = reverse("plotsearch-detail", kwargs={"pk": plot_search_test_data.id})
    response.data["targets"] = [
        {
            "plan_unit": plan_unit2.id,
            "target_type": PlotSearchTargetType.SEARCHABLE.value,
        },
    ]
    response = admin_client.put(
        url, data=json.dumps(response.data), content_type="application/json"
    )
    assert response.status_code == 200, "%s %s" % (response.status_code, response.data)

    # Confirm that the old duplicated plan unit has been deleted
    assert PlanUnit.objects.filter(id=duplicated_plan_unit_id).count() == 0
