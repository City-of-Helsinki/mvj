import pytest
from django.urls import reverse

from leasing.enums import PlotSearchTargetType
from plotsearch.models import PlotSearchTarget
from plotsearch.models.plot_search import DirectReservationLink, Favourite


@pytest.mark.django_db
def test_direct_reservation_link_create(
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

    target = PlotSearchTarget.objects.create(
        plot_search=plot_search_test_data,
        plan_unit=plan_unit,
        target_type=PlotSearchTargetType.DIRECT_RESERVATION,
    )

    data = {
        "targets": [target.id],
    }

    url = reverse("directreservationlink-list")

    response = admin_client.post(url, data, content_type="application/json")

    assert response.status_code == 201, "%s %s" % (response.status_code, response.data)
    assert len(DirectReservationLink.objects.all()) > 0


@pytest.mark.django_db
def test_direct_reservation_link_delete(
    django_db_setup,
    plan_unit_factory,
    lease_test_data,
    plot_search_test_data,
    admin_client,
):
    # Attach plan unit for plot search
    plan_unit = plan_unit_factory(
        identifier="PU1",
        area=1000,
        lease_area=lease_test_data["lease_area"],
        is_master=True,
    )

    target = PlotSearchTarget.objects.create(
        plot_search=plot_search_test_data,
        plan_unit=plan_unit,
        target_type=PlotSearchTargetType.DIRECT_RESERVATION,
    )

    direct_reservation_link = DirectReservationLink.objects.create()
    direct_reservation_link.targets.add(target)

    url = reverse(
        "directreservationlink-detail", kwargs={"pk": direct_reservation_link.uuid}
    )
    response = admin_client.delete(url)

    assert response.status_code == 204, "%s %s" % (response.status_code, response.data)
    assert len(DirectReservationLink.objects.all()) == 0


@pytest.mark.django_db
def test_create_favourites_with_link(
    django_db_setup,
    admin_client,
    lease_test_data,
    plot_search_test_data,
    plan_unit_factory,
):
    # Attach plan units for plot search
    direct_reservation_link = DirectReservationLink.objects.create()

    for i in range(3):
        direct_reservation_link.targets.add(
            PlotSearchTarget.objects.create(
                plot_search=plot_search_test_data,
                plan_unit=plan_unit_factory(
                    identifier="PU{}".format(i),
                    area=1000,
                    lease_area=lease_test_data["lease_area"],
                    is_master=True,
                ),
                target_type=PlotSearchTargetType.DIRECT_RESERVATION,
            )
        )

    url = reverse(
        "pub_direct_reservation_to_favourite",
        kwargs={"uuid": direct_reservation_link.uuid},
    )
    response = admin_client.get(url)

    assert response.status_code == 200, "%s %s" % (response.status_code, response.data)

    favourite = Favourite.objects.get(user=response.wsgi_request.user)
    assert (
        favourite.targets.all()[0].plot_search_target.id
        == plot_search_test_data.plot_search_targets.all()[0].id
    )
    assert len(favourite.targets.all()) == 3
