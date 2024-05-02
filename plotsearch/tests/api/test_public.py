import pytest
from faker import Faker
from rest_framework.reverse import reverse

from plotsearch.models.plot_search import FAQ

fake = Faker("fi_FI")


@pytest.mark.django_db
def test_faq_list(client):
    FAQ.objects.create(question=fake.name(), answer=fake.name())

    url = reverse("v1:pub_faq-list")

    response = client.get(path=url, content_type="application/json")

    assert response.status_code == 200
