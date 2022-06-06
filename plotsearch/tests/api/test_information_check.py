import pytest
from faker import Faker
from rest_framework.reverse import reverse

fake = Faker("fi_FI")


@pytest.mark.django_db
@pytest.mark.enable_signals
def test_information_check(admin_client, admin_user, basic_answer):
    url = reverse("informationcheck-list")

    response = admin_client.get(url)
    assert response.status_code == 200
    assert len(response.data["results"]) > 0
