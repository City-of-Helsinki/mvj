import json

import pytest
from django.core.serializers.json import DjangoJSONEncoder
from django.urls import reverse
from django.utils import timezone
from rest_framework import serializers

from leasing.enums import PlotSearchTargetType


@pytest.mark.django_db
def test_plot_search_detail(django_db_setup, admin_client, plot_search_test_data):

    url = reverse("plotsearch-detail", kwargs={"pk": plot_search_test_data.id})

    response = admin_client.get(url, content_type="application/json")
    assert response.status_code == 200, "%s %s" % (response.status_code, response.data)


@pytest.mark.django_db
def test_plot_search_list(django_db_setup, admin_client, plot_search_test_data):

    url = reverse("plotsearch-list")

    response = admin_client.get(url, content_type="application/json")
    assert response.status_code == 200, "%s %s" % (response.status_code, response.data)


@pytest.mark.django_db
def test_plot_search_create(
    django_db_setup, admin_client, plot_search_test_data, lease_test_data, user_factory
):
    url = reverse("plotsearch-list")  # list == create

    user = user_factory(username="test_user")
    selected_planunit = (
        lease_test_data["lease_area"].plan_units.filter(in_contract=True).first()
    )

    data = {
        "name": plot_search_test_data.type.name,
        "type": plot_search_test_data.type.id,
        "subtype": plot_search_test_data.subtype.id,
        "stage": plot_search_test_data.stage.id,
        "preparer": user.id,
        "begin_at": timezone.now(),
        "end_at": timezone.now() + timezone.timedelta(days=7),
        "targets": [
            {
                "plan_unit": selected_planunit.id,
                "target_type": PlotSearchTargetType.SEARCHABLE.value,
            },
        ],
    }

    response = admin_client.post(
        url, json.dumps(data, cls=DjangoJSONEncoder), content_type="application/json"
    )
    assert response.status_code == 201, "%s %s" % (response.status_code, response.data)
    assert len(response.data["targets"]) > 0


@pytest.mark.django_db
def test_plot_search_update(
    django_db_setup, admin_client, plot_search_test_data, lease_test_data, user_factory
):
    url = reverse(
        "plotsearch-detail", kwargs={"pk": plot_search_test_data.id}
    )  # detail == update

    user = user_factory(username="test_user")
    selected_planunit = (
        lease_test_data["lease_area"].plan_units.filter(in_contract=True).first()
    )
    updated_end_at = plot_search_test_data.end_at + timezone.timedelta(days=30)

    data = {
        "name": plot_search_test_data.type.name,
        "type": plot_search_test_data.type.id,
        "subtype": plot_search_test_data.subtype.id,
        "stage": plot_search_test_data.stage.id,
        "preparer": user.id,
        "begin_at": plot_search_test_data.begin_at,
        "end_at": updated_end_at,
        "targets": [
            {
                "plan_unit": selected_planunit.id,
                "target_type": PlotSearchTargetType.SEARCHABLE.value,
            },
        ],
    }

    response = admin_client.put(url, data=data, content_type="application/json")
    assert response.status_code == 200, "%s %s" % (response.status_code, response.data)
    assert response.data["end_at"] == serializers.DateTimeField().to_representation(
        updated_end_at
    )
    assert len(response.data["targets"]) > 0
