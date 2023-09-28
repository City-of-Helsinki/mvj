import json
import os
from unittest.mock import patch

import pytest
from django.contrib.auth.models import Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import timezone
from faker import Faker

from forms.enums import FormState
from forms.models import Entry, Field
from forms.models.form import AnswerOpeningRecord, Attachment
from plotsearch.enums import DeclineReason
from plotsearch.models import TargetStatus

fake = Faker("fi_FI")

BOUNDARY = "!! test boundary !!"


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
    subsection_data = {
        "title": fake.name(),
        "form": basic_form.id,
        "identifier": "henkilon-tiedot",
    }
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
    url = reverse("pub_answer-list")  # Use public endpoint for posting answers
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
                            "fields": {"company-name": {"value": "", "extraValue": ""}},
                        },
                        {
                            "sections": {},
                            "fields": {
                                "business-id": {
                                    "value": "",
                                    "extraValue": "",
                                    "hallintaosuus": {"value": "1/1", "extraValue": ""},
                                }
                            },
                        },
                    ],
                    "hakijan-tiedot": {
                        "sections": {
                            "contact-person": {
                                "sections": {},
                                "fields": {
                                    "first-name": {"value": "False", "extraValue": ""},
                                    "last-name": {
                                        "value": "99",
                                        "extraValue": "developers developers developers",
                                    },
                                },
                            },
                        },
                        "fields": {},
                    },
                },
                "fields": {},
                "metadata": {"metaa": "on"},
            }
        ),
        "attachments": [],
        "ready": True,
    }
    with patch("forms.utils.async_task") as mock_async_task:
        response = admin_client.post(url, data=payload)

    assert response.status_code == 201
    assert len(Entry.objects.all()) == 4
    assert mock_async_task.called, "async_task was not called to generate emails"
    _, async_task_kwargs = mock_async_task.call_args
    assert async_task_kwargs.get("input_data").get("answer_id") == response.data["id"]

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
                            "company-name": {
                                "value": "jee",
                                "extraValue": "",
                                "hallintaosuus": {"value": "1/1", "extraValue": ""},
                            }
                        },
                    },
                ],
                "hakijan-tiedot": {
                    "sections": {
                        "contact-person": {
                            "sections": {},
                            "fields": {
                                "first-name": {"value": "Matti", "extraValue": ""},
                                "last-name": {
                                    "value": "99",
                                    "extraValue": "developers developers developers",
                                },
                            },
                        },
                    },  # fmt: on
                    "fields": {},
                },
            },
            "fields": {},
            "metadata": {"metaa": "on"},
        },
        "ready": True,
    }
    response = admin_client.patch(url, data=payload, content_type="application/json")
    patched_data = response.data["entries_data"]
    assert response.status_code == 200
    assert (
        patched_data["hakijan-tiedot"]["contact-person"]["fields"]["first-name"][
            "value"
        ]
        == "Matti"
    )
    assert patched_data["hakijan-tiedot"]["metadata"] == {"metaa": "on"}

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
def test_target_status_patch(
    django_db_setup,
    client,
    answer_factory,
    area_search_test_data,
    basic_template_form,
    plot_search_target,
    user,
):
    answer = answer_factory(form=basic_template_form, user=user)
    plot_search_target.answers.add(answer)
    plot_search_target.save()

    target_status_data = {
        "identifier": "91-21-21-21",
        "share_of_rental_indicator": 2,
        "share_of_rental_denominator": 3,
        "reserved": True,
        "added_target_to_applicant": True,
        "counsel_date": timezone.now(),
        "decline_reason": DeclineReason.APPLICATION_REVOKED,
        "arguments": "Very good arguments",
        "proposed_managements": [],
        "reservation_conditions": ["Very good condition",],  # noqa: E231
        "geometry": area_search_test_data.geometry.geojson,
    }

    target_status = TargetStatus.objects.all().first()

    preparer = target_status.plot_search_target.plot_search.preparers.first()
    preparer.user_permissions.add(
        Permission.objects.get(
            content_type__model="targetstatus", name__contains="change"
        )
    )

    client.force_login(target_status.plot_search_target.plot_search.preparers.first())

    url = reverse("targetstatus-detail", kwargs={"pk": target_status.pk})
    response = client.patch(
        url, data=target_status_data, content_type="application/json"
    )

    assert response.status_code == 200
    assert TargetStatus.objects.all().first().share_of_rental_indicator == 2


def test_meeting_memo_create(
    django_db_setup,
    admin_client,
    answer_factory,
    area_search_test_data,
    basic_template_form,
    plot_search_target,
    user,
):
    answer = answer_factory(form=basic_template_form, user=user)
    plot_search_target.answers.add(answer)
    plot_search_target.save()

    target_status = TargetStatus.objects.all().first()
    target_status.counsel_date = timezone.now()
    target_status.save()

    meeting_memo = {
        "target_status": target_status.id,
        "meeting_memo": SimpleUploadedFile(content=b"Lorem Impsum", name="test.txt"),
        "name": fake.name(),
    }

    url = reverse("meetingmemo-list",)
    response = admin_client.post(url, data=meeting_memo)

    assert response.status_code == 201

    url = reverse(
        "answer-detail", kwargs={"pk": TargetStatus.objects.all().first().answer.pk}
    )
    response = admin_client.get(url)

    assert len(response.data["target_statuses"][0]["meeting_memos"]) == 1


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
                        "fields": {"company-name": {"value": "", "extraValue": ""}},
                    },
                    {
                        "sections": {},
                        "fields": {
                            "business-id": {"value": "", "extraValue": ""},
                            "hallintaosuus": {"value": "1/1", "extraValue": ""},
                        },
                    },
                ],
                "contact-person": {
                    "sections": {},
                    "fields": {
                        "first-name": {"value": "False", "extraValue": ""},
                        "last-name": {
                            "value": "99",
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


@pytest.mark.django_db
def test_opening_record_create(
    django_db_setup,
    client,
    user,
    user_factory,
    answer_factory,
    plot_search_target,
    basic_template_form,
):
    answer = answer_factory(form=basic_template_form, user=user)
    plot_search_target.answers.add(answer)
    plot_search_target.save()

    not_authorized_user = user_factory()

    opening_record = {
        "openers": [
            plot_search_target.plot_search.preparers.all().first().pk,  # noqa: E231
        ],
        "answer": answer.pk,
    }

    url = reverse("answer_opening_record-list")
    response = client.post(url, data=opening_record)
    assert response.status_code == 401

    client.force_login(not_authorized_user)
    response = client.post(url, data=opening_record)
    assert response.status_code == 403

    client.force_login(plot_search_target.plot_search.preparers.all().first())
    response = client.post(url, data=opening_record)
    assert response.status_code == 201


@pytest.mark.django_db
def test_opening_record_permissions(
    django_db_setup,
    client,
    user,
    user_factory,
    answer_factory,
    plot_search_target,
    basic_template_form,
):
    answer = answer_factory(form=basic_template_form, user=user)
    plot_search_target.answers.add(answer)
    plot_search_target.save()

    not_authorized_user = user_factory()

    opening_record = {
        "openers": [
            plot_search_target.plot_search.preparers.all().first().pk,  # noqa: E231
        ],
        "answer": answer.pk,
    }

    url = reverse("answer_opening_record-list")

    client.force_login(not_authorized_user)
    response = client.post(url, data=opening_record)
    assert response.status_code == 403

    not_authorized_user.user_permissions.add(
        Permission.objects.get(codename="add_answeropeningrecord")
    )

    client.force_login(not_authorized_user)
    response = client.post(url, data=opening_record)
    assert response.status_code == 201

    id = response.data["id"]
    patch_url = reverse("answer_opening_record-detail", kwargs={"pk": id})

    response = client.patch(
        patch_url, data=opening_record, content_type="application/json"
    )
    assert response.status_code == 403

    not_authorized_user.user_permissions.add(
        Permission.objects.get(codename="change_answeropeningrecord")
    )

    client.force_login(not_authorized_user)
    response = client.patch(
        patch_url, data=opening_record, content_type="application/json"
    )
    assert response.status_code == 200


@pytest.mark.django_db
def test_answer_permissions_when_not_needed_opening_record(
    django_db_setup,
    client,
    user,
    user_factory,
    answer_factory,
    plot_search_target,
    basic_template_form,
):
    answer = answer_factory(form=basic_template_form, user=user)
    plot_search_target.answers.add(answer)
    plot_search_target.save()

    type = plot_search_target.plot_search.subtype
    type.require_opening_record = True
    type.save()

    url = reverse("answer-detail", kwargs={"pk": answer.pk})

    client.force_login(plot_search_target.plot_search.preparers.all().first())
    response = client.get(url)
    assert response.status_code == 403

    type.require_opening_record = False
    type.save()

    response = client.get(url)
    assert response.status_code == 200


@pytest.mark.django_db
def test_opening_record_patch(
    django_db_setup,
    client,
    user,
    user_factory,
    answer_factory,
    plot_search_target,
    basic_template_form,
):
    answer = answer_factory(form=basic_template_form, user=user)
    plot_search_target.answers.add(answer)
    plot_search_target.save()

    opening_record = {
        "openers": [
            plot_search_target.plot_search.preparers.all().first().pk,  # noqa: E231
        ],
        "answer": answer.pk,
    }

    url = reverse("answer_opening_record-list")

    client.force_login(plot_search_target.plot_search.preparers.all().first())
    response = client.post(url, data=opening_record)
    assert response.status_code == 201

    id = response.data["id"]

    url = reverse("answer_opening_record-detail", kwargs={"pk": id})

    opening_record = {
        "openers": [
            plot_search_target.plot_search.preparers.all().first().pk,  # noqa: E231
        ],
        "answer": answer.pk,
        "note": "Hakijana on Yritys oy",
    }

    response = client.patch(url, data=opening_record, content_type="application/json")
    assert response.status_code == 200
    assert AnswerOpeningRecord.objects.get(id=id).note == "Hakijana on Yritys oy"
