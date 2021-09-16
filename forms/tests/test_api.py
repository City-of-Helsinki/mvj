import pytest
from django.urls import reverse
from faker import Faker

fake = Faker("fi_FI")


@pytest.mark.django_db
def test_filter_form_is_template(django_db_setup, form_factory, admin_client):
    form_factory(
        name=fake.name(),
        description=fake.sentence(),
        is_template=True,
        title=fake.name(),
    )

    url = reverse("form-list")
    response_filter_true = admin_client.get(
        url, content_type="application/json", data={"is_template": True}
    )
    response_filter_false = admin_client.get(
        url, content_type="application/json", data={"is_template": False}
    )

    assert response_filter_true.data["count"] == 1
    assert response_filter_false.data["count"] == 0
