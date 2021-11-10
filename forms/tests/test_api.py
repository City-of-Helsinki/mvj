import pytest
from django.urls import reverse
from faker import Faker

from forms.enums import FormState

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


@pytest.mark.django_db
def test_edit_form(admin_client, basic_form):
    url = reverse("form-detail", kwargs={"pk": basic_form.id})
    payload = {"state": FormState.READY}
    response = admin_client.patch(url, payload, content_type="application/json")
    assert response.status_code == 200
    assert response.data["state"] == FormState.READY


@pytest.mark.django_db
def test_delete_form(admin_client, basic_form):
    url = reverse("form-detail", kwargs={"pk": basic_form.id})
    response = admin_client.delete(url)
    assert response.status_code == 204


@pytest.mark.django_db
def test_add_field_to_form(admin_client, basic_form, basic_field_types):
    url = reverse("form-detail", kwargs={"pk": basic_form.id})
    response = admin_client.get(url)
    assert response.status_code == 200
    payload = response.data
    field_data = {
        "label": fake.name(),
        "hint_text": fake.sentence(),
        "validation": fake.sentence(),
        "action": fake.sentence(),
        "type": basic_field_types["textarea"].id,
        "section": payload["sections"][0]["id"],
    }

    prev_fields_len = len(payload["sections"][0]["fields"])
    payload["sections"][0]["fields"].append(field_data)
    response = admin_client.patch(url, data=payload, content_type="application/json",)
    assert response.status_code == 200
    response = admin_client.get(url)
    assert response.status_code == 200
    assert len(response.data["sections"][0]["fields"]) - 1 == prev_fields_len


@pytest.mark.django_db
def test_add_and_delete_section_to_form(admin_client, basic_form):
    url = reverse("form-detail", kwargs={"pk": basic_form.id})
    response = admin_client.get(url)
    assert response.status_code == 200
    payload = response.data
    sections_count = len(payload["sections"])
    subsection_data = {"title": fake.name(), "form": basic_form.id}
    section_data = {
        "title": fake.name(),
        "form": basic_form.id,
        "subsections": [subsection_data],
    }

    payload["sections"].append(section_data)
    response = admin_client.patch(url, data=payload, content_type="application/json")
    assert response.status_code == 200
    assert len(response.data["sections"]) - 1 == sections_count

    payload = response.data
    payload["sections"].pop()
    response = admin_client.patch(url, data=payload, content_type="application/json")
    assert response.status_code == 200
    assert len(response.data["sections"]) == sections_count
