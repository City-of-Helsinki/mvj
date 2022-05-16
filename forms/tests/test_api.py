import json
import os

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from faker import Faker

from forms.enums import FormState
from forms.models import Entry, Field
from forms.models.form import Attachment

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


@pytest.mark.django_db
def test_answer_post(
    django_db_setup,
    admin_client,
    admin_user,
    plot_search_target,
    client,
    user_factory,
    basic_form,
):
    url = reverse("answer-list")
    payload = {
        "form": basic_form.id,
        "user": admin_user.pk,
        "targets": [plot_search_target.pk,],  # noqa: E231
        "entries": json.dumps(
            {
                "sections": {
                    "company-information": [
                        {
                            "sections": {},
                            "fields": {
                                "company-name": {"value": "", "extraValue": None}
                            },
                        },
                        {
                            "sections": {},
                            "fields": {
                                "business-id": {"value": "", "extraValue": None}
                            },
                        },
                    ],
                    "contact-person": {
                        "sections": {},
                        "fields": {
                            "first-name": {"value": False, "extraValue": None},
                            "last-name": {
                                "value": 99,
                                "extraValue": "developers developers developers",
                            },
                        },
                    },
                },
                "fields": {},
            }
        ),
        "attachments": [],
        "ready": True,
    }
    response = admin_client.post(url, data=payload)

    assert response.status_code == 201
    assert len(Entry.objects.all()) == 4

    url = reverse("answer-detail", kwargs={"pk": 1})
    payload = {
        "form": basic_form.id,
        "user": admin_user.pk,
        "entries": {
            "sections": {
                "company-information": [
                    {
                        "sections": {},
                        "fields": {
                            "company-name": {"value": "jee", "extraValue": None}
                        },
                    },
                ],
                "contact-person": {
                    "sections": {},  # fmt:off
                    "fields": {
                        "first-name": {"value": "Matti", "extraValue": None},
                    },  # Formatting bug
                },  # fmt: on
            },
            "fields": {},
        },
        "ready": True,
    }
    response = admin_client.patch(url, data=payload, content_type="application/json")
    patched_data = response.data["entries_data"]
    assert response.status_code == 200
    assert patched_data["contact-person"]["fields"]["first-name"]["value"] == "Matti"

    url = reverse("answer-list")
    response = admin_client.get(url)
    assert response.status_code == 200

    user = user_factory()
    password = "test"
    user.set_password(password)
    user.save()
    client.login(username=user.username, password=password)

    url = reverse("answer-list")
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_attachment_post(
    django_db_setup, admin_client, admin_user, plot_search_target, basic_form
):
    example_file = SimpleUploadedFile(name="example.txt", content=b"Lorem lipsum")
    payload = {
        "field": Field.objects.all().first().id,
        "name": fake.name(),
        "attachment": example_file,
    }
    url = reverse("attachment-list")
    response = admin_client.post(url, data=payload)
    assert response.status_code == 201
    attachment_id = response.json()["id"]

    url = reverse("answer-list")
    payload = {
        "form": basic_form.id,
        "user": admin_user.pk,
        "targets": [plot_search_target.pk,],  # noqa: E231
        "entries": {
            "sections": {
                "company-information": [
                    {
                        "sections": {},
                        "fields": {"company-name": {"value": "", "extraValue": None}},
                    },
                    {
                        "sections": {},
                        "fields": {"business-id": {"value": "", "extraValue": None}},
                    },
                ],
                "contact-person": {
                    "sections": {},
                    "fields": {
                        "first-name": {"value": False, "extraValue": None},
                        "last-name": {
                            "value": 99,
                            "extraValue": "developers developers developers",
                        },
                    },
                },
            },
            "fields": {},
        },
        "attachments": [attachment_id,],  # noqa: E231
        "ready": True,
    }
    response = admin_client.post(url, data=payload, content_type="application/json")
    id = response.json()["id"]

    assert response.status_code == 201
    assert Attachment.objects.filter(answer=response.json()["id"]).exists()

    url = reverse("answer-attachments", kwargs={"pk": id})
    response = admin_client.get(url)
    url = reverse("attachment-download", kwargs={"pk": attachment_id})
    file_request = admin_client.get(url)
    assert response.status_code == 200
    assert len(response.json()) != 0
    assert file_request.status_code == 200
    assert file_request.content == b"Lorem lipsum"


@pytest.mark.django_db
def test_attachment_delete(
    django_db_setup, admin_client, admin_user, plot_search_target, basic_form
):
    test_attachment_post(
        django_db_setup, admin_client, admin_user, plot_search_target, basic_form
    )
    attachment = Attachment.objects.all().first()
    url = reverse("attachment-detail", kwargs={"pk": attachment.pk})
    file_path = attachment.attachment.path
    assert os.path.isfile(file_path) is True
    response = admin_client.delete(url)
    assert response.status_code == 204
    assert os.path.isfile(file_path) is False
