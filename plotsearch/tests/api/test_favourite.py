import pytest
from django.urls import reverse
from django.utils import timezone
from faker import Faker

from leasing.enums import PlotSearchTargetType
from plotsearch.models import Favourite, FavouriteTarget, PlotSearchTarget
from users.models import User

fake = Faker("fi_FI")


@pytest.mark.django_db
def test_favourite_detail(
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
    pls = PlotSearchTarget.objects.create(
        plot_search=plot_search_test_data,
        plan_unit=plan_unit,
        target_type=PlotSearchTargetType.SEARCHABLE,
    )

    fav = Favourite.objects.create(user=User.objects.get(username="admin"))
    FavouriteTarget.objects.create(favourite=fav, plot_search_target=pls)

    url = reverse("favourite-detail", kwargs={"pk": fav.pk})

    response = admin_client.get(url, content_type="application/json")
    assert response.status_code == 200, "%s %s" % (response.status_code, response.data)


@pytest.mark.django_db
def test_favourite_list(django_db_setup, admin_client, plot_search_test_data):

    url = reverse("favourite-list")

    response = admin_client.get(url, content_type="application/json")
    assert response.status_code == 200, "%s %s" % (response.status_code, response.data)


@pytest.mark.django_db
def test_favourite_post(
    django_db_setup,
    admin_client,
    plan_unit_factory,
    plot_search_test_data,
    lease_test_data,
):

    url = reverse("favourite-list")

    plan_unit = plan_unit_factory(
        identifier="PU1",
        area=1000,
        lease_area=lease_test_data["lease_area"],
        is_master=True,
    )

    pls = PlotSearchTarget.objects.create(
        plot_search=plot_search_test_data,
        plan_unit=plan_unit,
        target_type=PlotSearchTargetType.SEARCHABLE,
    )

    pls_target = dict()
    pls_target["plot_search_target"] = pls.pk

    data = {
        "user": User.objects.get(username="admin").pk,
        "targets": [{"plot_search_target": pls.pk}],
    }

    response = admin_client.post(url, data, content_type="application/json")
    assert response.status_code == 201, "%s %s" % (response.status_code, response.data)

    fav = Favourite.objects.first()

    url = reverse("favourite-detail", kwargs={"pk": fav.pk})

    data = {"modified_at": timezone.now()}
    response = admin_client.patch(url, data, content_type="application/json")
    assert response.status_code == 200, "%s %s" % (response.status_code, response.data)
