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


@pytest.mark.django_db
def test_delete_form(admin_client, basic_form):
    url = reverse("form-detail", kwargs={"pk": basic_form.id})
    response = admin_client.delete(url)
    assert response.status_code == 204


@pytest.mark.django_db
def test_add_field_to_form(admin_client, basic_form, basic_field_types):
    section = basic_form.sections.first()
    field_data = {
        "label": fake.name(),
        "hint_text": fake.sentence(),
        "validation": fake.sentence(),
        "action": fake.sentence(),
        "type": basic_field_types["textarea"].id,
        "section": section.id,
    }

    url = reverse("field-list")
    response = admin_client.post(url, field_data)
    created_id = response.data["id"]
    assert response.status_code == 201

    url = reverse("section-detail", kwargs={"pk": section.id})
    response = admin_client.get(url)
    assert response.status_code == 200

    field_in_section = False
    for field in response.data["fields"]:
        if "id" in field and field["id"] == created_id:
            field_in_section = True
            return

    assert field_in_section
