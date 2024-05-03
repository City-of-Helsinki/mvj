import pytest
from faker import Faker
from rest_framework.reverse import reverse

from plotsearch.models import InformationCheck

fake = Faker("fi_FI")


@pytest.mark.django_db
@pytest.mark.enable_signals
def test_information_check(admin_client, admin_user, basic_answer):
    url = reverse("v1:informationcheck-list")

    response = admin_client.get(url)
    assert response.status_code == 200
    assert len(response.data["results"]) > 0

    data = {
        "mark_all": False,
        "state": "checked",
        "preparer": admin_user.pk,
        "comment": "test",
    }
    url = reverse(
        "v1:informationcheck-detail",
        kwargs={"pk": InformationCheck.objects.all().first().pk},
    )
    response = admin_client.patch(url, data=data, content_type="application/json")
    assert response.status_code == 200
    assert response.data["comment"] == "test"

    url = reverse("v1:answer-list")

    response = admin_client.get(url)
    assert response.status_code == 200
    assert len(response.data["results"]) > 0
