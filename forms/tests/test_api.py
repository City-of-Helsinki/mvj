import json
import os
from unittest.mock import patch

import pytest
from django.contrib.auth.models import Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import FileResponse
from django.test import override_settings
from django.urls import NoReverseMatch, reverse
from django.utils import timezone
from faker import Faker

from forms.enums import FormState
from forms.models import Entry
from forms.models.form import AnswerOpeningRecord, Attachment
from forms.serializers.form import EXCLUDED_ATTACHMENT_FIELDS
from mvj.tests.test_urls import set_plotsearch_flag_reload_urlconf  # noqa: F401
from plotsearch.enums import DeclineReason
from plotsearch.models import TargetStatus

fake = Faker("fi_FI")

BOUNDARY = "!! test boundary !!"


@pytest.mark.django_db
def test_filter_form_is_template(django_db_setup, form_factory, admin_client):
    template_form = form_factory(
        name=fake.name(),
        description=fake.sentence(),
        is_template=True,
        title=fake.name(),
    )

    url = reverse("v1:form-list")
    response_filter_true = admin_client.get(
        url, content_type="application/json", data={"is_template": True}
    )
    response_filter_false = admin_client.get(
        url, content_type="application/json", data={"is_template": False}
    )

    template_form_ids = (form["id"] for form in response_filter_true.data["results"])
    # Should find template form.
    assert template_form.id in template_form_ids

    form_ids = (form["id"] for form in response_filter_false.data["results"])
    # Should not find template form.
    assert template_form.id not in form_ids


@pytest.mark.django_db
def test_edit_form(admin_client, basic_form):
    url = reverse("v1:form-detail", kwargs={"pk": basic_form.id})
    payload = {"state": FormState.READY}
    response = admin_client.patch(url, payload, content_type="application/json")
    assert response.status_code == 200
    assert response.data["state"] == FormState.READY


@pytest.mark.django_db
def test_delete_form(admin_client, basic_form):
    url = reverse("v1:form-detail", kwargs={"pk": basic_form.id})
    response = admin_client.delete(url)
    assert response.status_code == 204


@pytest.mark.django_db
def test_add_field_to_form(admin_client, basic_form):
    url = reverse("v1:form-detail", kwargs={"pk": basic_form.id})
    response = admin_client.get(url)
    assert response.status_code == 200
    payload = response.data
    field_data = {
        "label": fake.name(),
        "hint_text": fake.sentence(),
        "validation": fake.sentence(),
        "action": fake.sentence(),
        "type": "textarea",
        "section": payload["sections"][0]["id"],
    }

    prev_fields_len = len(payload["sections"][0]["fields"])
    payload["sections"][0]["fields"].append(field_data)
    response = admin_client.patch(
        url,
        data=payload,
        content_type="application/json",
    )
    assert response.status_code == 200
    response = admin_client.get(url)
    assert response.status_code == 200
    assert len(response.data["sections"][0]["fields"]) - 1 == prev_fields_len


@pytest.mark.django_db
def test_add_and_delete_section_to_form(admin_client, basic_form):
    url = reverse("v1:form-detail", kwargs={"pk": basic_form.id})
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
    url = reverse("v1:pub_answer-list")  # Use public endpoint for posting answers
    payload = {
        "form": basic_form.id,
        "user": admin_user.pk,
        "targets": [
            plot_search_target.pk,
        ],  # noqa: E231
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
    answer_id = async_task_kwargs.get("input_data").get("answer_id")
    assert answer_id == response.data["id"]

    url = reverse("v1:answer-detail", kwargs={"pk": answer_id})
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

    url = reverse("v1:answer-list")
    response = admin_client.get(url)
    assert response.status_code == 200

    user = user_factory()
    password = "test"
    user.set_password(password)
    user.save()
    client.login(username=user.username, password=password)

    url = reverse("v1:answer-list")
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
        "decline_reason": DeclineReason.APPLICATION_EXPIRED,
        "arguments": "Very good arguments",
        "proposed_managements": [],
        "reservation_conditions": [
            "Very good condition",
        ],  # noqa: E231
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

    url = reverse("v1:targetstatus-detail", kwargs={"pk": target_status.pk})
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

    url = reverse(
        "v1:meetingmemo-list",
    )
    response = admin_client.post(url, data=meeting_memo)

    assert response.status_code == 201

    url = reverse(
        "v1:answer-detail", kwargs={"pk": TargetStatus.objects.all().first().answer.pk}
    )
    response = admin_client.get(url)

    assert len(response.data["target_statuses"][0]["meeting_memos"]) == 1


@pytest.mark.django_db
def test_attachment_post(
    django_db_setup, admin_client, admin_user, plot_search_target, basic_form
):
    example_file = SimpleUploadedFile(name="example.txt", content=b"Lorem lipsum")
    field = basic_form.sections.get(identifier="application-target").fields.get(
        identifier="reference-attachments"
    )
    payload = {
        "field": field.id,
        "name": fake.name(),
        "attachment": example_file,
    }
    url = reverse("v1:attachment-list")
    response = admin_client.post(url, data=payload)
    assert response.status_code == 201
    attachment_id = response.json()["id"]

    url = reverse("v1:answer-list")
    payload = {
        "form": basic_form.id,
        "user": admin_user.pk,
        "targets": [
            plot_search_target.pk,
        ],  # noqa: E231
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
        "attachments": [
            attachment_id,
        ],  # noqa: E231
        "ready": True,
    }
    response = admin_client.post(url, data=payload, content_type="application/json")
    answer_id = response.json()["id"]

    assert response.status_code == 201

    # Attachment should exist
    assert Attachment.objects.filter(answer=answer_id).exists()


@pytest.mark.django_db
def test_attachment_get(
    django_db_setup, admin_client, admin_user, answer_factory, attachment_factory
):
    answer = answer_factory()
    answer_id = answer.id
    example_file = SimpleUploadedFile(name="example.txt", content=b"Lorem lipsum")
    attachment = attachment_factory(
        user=admin_user, answer=answer, attachment=example_file
    )
    attachment_id = attachment.id

    # Should get attachments
    url = reverse("v1:answer-attachments", kwargs={"pk": answer_id})
    response = admin_client.get(url)
    assert response.status_code == 200
    assert len(response.json()) != 0

    # override_settings is necessary to avoid breaking this older test after the
    # virus/malware scanning mechanic was added to most file/attachment classes.
    with override_settings(FLAG_FILE_SCAN=False):
        url = reverse("v1:attachment-download", kwargs={"pk": attachment_id})
        file_response: FileResponse = admin_client.get(url)

    assert file_response.status_code == 200
    # Get the content from the generator
    assert b"".join(file_response.streaming_content) == b"Lorem lipsum"


@pytest.mark.django_db
def test_attachment_delete(
    django_db_setup, admin_client, admin_user, attachment_factory
):
    example_file = SimpleUploadedFile(name="example.txt", content=b"Lorem lipsum")
    attachment = attachment_factory(attachment=example_file, user=admin_user)
    url = reverse("v1:attachment-detail", kwargs={"pk": attachment.pk})
    file_path = attachment.attachment.path
    assert os.path.isfile(file_path) is True
    response = admin_client.delete(url)
    assert response.status_code == 204
    assert os.path.isfile(file_path) is False


@override_settings(FLAG_PLOTSEARCH=True)
@pytest.mark.django_db
def test_attachment_post_public(
    set_plotsearch_flag_reload_urlconf,  # noqa: F811
    django_db_setup,
    admin_client,
    admin_user,
    plot_search_target,
    basic_form,
):
    example_file = SimpleUploadedFile(name="example.txt", content=b"Lorem lipsum")
    field = basic_form.sections.get(identifier="application-target").fields.get(
        identifier="reference-attachments"
    )
    payload = {
        "field": field.id,
        "name": fake.name(),
        "attachment": example_file,
    }
    url = reverse("v1:pub_attachment-list")
    response = admin_client.post(url, data=payload)
    assert response.status_code == 201

    # When attachments are created,
    # the HTTP response should not return any sensitive or unnecessary data
    attachment_keys = response.json().keys()
    unwanted_fields_in_response = set(EXCLUDED_ATTACHMENT_FIELDS).intersection(
        set(attachment_keys)
    )
    assert len(unwanted_fields_in_response) == 0

    attachment_id = response.json()["id"]
    url = reverse("v1:pub_answer-list")
    payload = {
        "form": basic_form.id,
        "user": admin_user.pk,
        "targets": [
            plot_search_target.pk,
        ],  # noqa: E231
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
        "attachments": [
            attachment_id,
        ],  # noqa: E231
        "ready": True,
    }
    response = admin_client.post(url, data=payload, content_type="application/json")

    # When an answer is created, the HTTP response should not contain the key "attachments"
    assert "attachments" not in response.json().keys()

    # Attachment should exist
    assert response.status_code == 201
    assert Attachment.objects.filter(answer=response.json()["id"]).exists()


@override_settings(FLAG_PLOTSEARCH=True)
@pytest.mark.django_db
def test_attachment_get_public(
    set_plotsearch_flag_reload_urlconf,  # noqa: F811
    django_db_setup,
    admin_client,
    admin_user,
    answer_factory,
    attachment_factory,
):
    answer = answer_factory()
    answer_id = answer.id
    example_file = SimpleUploadedFile(name="example.txt", content=b"Lorem lipsum")
    attachment = attachment_factory(
        user=admin_user, answer=answer, attachment=example_file
    )
    attachment_id = attachment.id

    # Public endpoint should not allow getting attachments
    with pytest.raises(NoReverseMatch):
        reverse("v1:pub_answer-attachments", kwargs={"pk": answer_id})

    # Public endpoint should not allow downloading attachments
    with pytest.raises(NoReverseMatch):
        reverse("v1:pub_attachment-download", kwargs={"pk": attachment_id})


@override_settings(FLAG_PLOTSEARCH=True)
@pytest.mark.django_db
def test_attachment_delete_public(
    set_plotsearch_flag_reload_urlconf,  # noqa: F811
    django_db_setup,
    admin_user,
    admin_client,
    attachment_factory,
):
    example_file = SimpleUploadedFile(name="example.txt", content=b"Lorem lipsum")
    attachment = attachment_factory(attachment=example_file, user=admin_user)
    url = reverse("v1:pub_attachment-detail", kwargs={"pk": attachment.pk})
    file_path = attachment.attachment.path
    assert os.path.isfile(file_path) is True
    response = admin_client.delete(url)
    assert response.status_code == 405  # Method not allowed


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

    url = reverse("v1:answer_opening_record-list")
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

    url = reverse("v1:answer_opening_record-list")

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
    patch_url = reverse("v1:answer_opening_record-detail", kwargs={"pk": id})

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

    url = reverse("v1:answer-detail", kwargs={"pk": answer.pk})

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

    url = reverse("v1:answer_opening_record-list")

    client.force_login(plot_search_target.plot_search.preparers.all().first())
    response = client.post(url, data=opening_record)
    assert response.status_code == 201

    id = response.data["id"]

    url = reverse("v1:answer_opening_record-detail", kwargs={"pk": id})

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
