import pytest
from rest_framework.reverse import reverse


@pytest.mark.django_db
def test_user_list(user_factory, client, admin_client):
    user1 = user_factory()
    user_factory()

    client.force_login(user1)
    url = reverse("v1:user-list")
    response = client.get(url)
    assert len(response.json()["results"]) == 1
    assert response.json()["results"][0]["username"] == user1.username

    response = admin_client.get(url)
    assert len(response.json()["results"]) == 3
