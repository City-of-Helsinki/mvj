from unittest.mock import patch

import pytest
from django.conf import settings
from django.utils.translation import get_language

from forms.enums import AnswerType
from forms.models import Field, Section
from forms.utils import (
    AnswerInputData,
    clone_object,
    generate_and_queue_answer_emails,
)
from utils.email import EmailMessageInput

BASIC_TEMPLATE_SECTION_COUNT = 7
BASIC_TEMPLATE_FIELD_COUNT = 23


@pytest.mark.django_db
def test_form_cloning(basic_template_form):
    section_count = Section.objects.all().count()
    field_count = Field.objects.all().count()

    new_form = clone_object(basic_template_form)

    new_section_count = Section.objects.all().count()
    new_field_count = Field.objects.all().count()

    assert new_form.id != basic_template_form
    assert (
        new_section_count == section_count + BASIC_TEMPLATE_SECTION_COUNT
    ), "Cloning should add 7 sections"
    assert (
        new_field_count == field_count + BASIC_TEMPLATE_FIELD_COUNT
    ), "Cloning should add 23 fields"


@pytest.mark.django_db
def test_generate_and_send_applicant_and_lessor_emails(
    answer_with_email, setup_lessor_contacts_and_service_units
):
    """Answer email should be sent to both the applicant and the lessor."""
    answer = answer_with_email.get("answer")
    input_data: AnswerInputData = {
        "answer_id": answer.get("id"),
        "answer_type": AnswerType.AREA_SEARCH,
        "user_language": "fi",
    }
    with patch("forms.utils.send_email") as mock_send_answer_email, patch(
        "forms.utils._generate_applicant_plotsearch_email"
    ) as mock_generate_applicant_plotsearch_email, patch(
        "forms.utils._generate_lessor_new_areasearch_email"
    ) as mock_generate_lessor_new_areasearch_email:
        generate_and_queue_answer_emails(input_data=input_data)

        mock_generate_applicant_plotsearch_email.assert_called_once()
        mock_generate_lessor_new_areasearch_email.assert_called_once()
        assert len(mock_send_answer_email.call_args_list) == 2


@pytest.mark.django_db
def test_generate_and_queue_answer_emails(
    answer_with_email, setup_lessor_contacts_and_service_units
):
    answer = answer_with_email.get("answer")

    # Case 1: Test that async_task is called, content language is Finnish
    with patch("forms.utils.send_email") as mock_send_answer_email:
        input_data: AnswerInputData = {
            "answer_id": answer.get("id"),
            "answer_type": AnswerType.AREA_SEARCH,
            "user_language": "fi",
        }
        generate_and_queue_answer_emails(input_data=input_data)

        assert mock_send_answer_email.called
        (applicant_input,) = mock_send_answer_email.call_args_list[0].args
        applicant_email: EmailMessageInput = applicant_input
        assert applicant_email.get("from_email") == settings.DEFAULT_FROM_EMAIL
        assert (
            "Tämä on kopio Helsingin kaupungille lähetetystä aluehaun hakemuksesta."
            in applicant_email.get("body")
        ), "Should contain Finnish text from the email template"

    # Case 1: Test that async_task is called, content language is English
    with patch("forms.utils.send_email") as mock_send_answer_email:
        input_data: AnswerInputData = {
            "answer_id": answer.get("id"),
            "answer_type": AnswerType.AREA_SEARCH,
            "user_language": "en",
        }
        generate_and_queue_answer_emails(input_data=input_data)

        assert mock_send_answer_email.called
        (applicant_input,) = mock_send_answer_email.call_args_list[0].args
        applicant_email: EmailMessageInput = applicant_input
        assert applicant_email.get("from_email") == settings.DEFAULT_FROM_EMAIL
        assert (
            "This is a copy of your area search application sent to the City of Helsinki."
            in applicant_email.get("body")
        ), "Should contain English text from the email template"


@pytest.mark.django_db
def test_generate_email_user_language(
    answer_with_email, setup_lessor_contacts_and_service_units
):
    answer_id = answer_with_email.get("answer", {}).get("id")
    default_user_language = "fi"

    # Case 1: User language is set to Finnish
    with patch("forms.utils.override") as mock_override:
        user_language = "fi"
        input_data: AnswerInputData = {
            "answer_id": answer_id,
            "answer_type": AnswerType.AREA_SEARCH,
            "user_language": user_language,
        }
        generate_and_queue_answer_emails(input_data=input_data)
        assert mock_override.called
        language_code = mock_override.call_args_list[0].args[0]
        assert language_code == user_language

    # Case 2: User language is set to Georgian, should default to Finnish
    with patch("forms.utils.override") as mock_override:
        user_language = "ka"  # Georgian
        input_data: AnswerInputData = {
            "answer_id": answer_id,
            "answer_type": AnswerType.AREA_SEARCH,
            "user_language": user_language,
        }
        generate_and_queue_answer_emails(input_data=input_data)
        assert mock_override.called
        language_code = mock_override.call_args_list[0].args[0]
        assert language_code == default_user_language

    def get_language_side_effect(*args, **kwargs):
        # Check the active language when patched function is called
        assert get_language() == user_language

    # Case 3: User language is set to Swedish
    # Expecting the current language context to be Swedish
    with patch(
        "forms.utils._generate_applicant_plotsearch_email",
        side_effect=get_language_side_effect,
    ) as mock_generate_plotsearch_email:
        user_language = "sv"
        input_data: AnswerInputData = {
            "answer_id": answer_id,
            "answer_type": AnswerType.AREA_SEARCH,
            "user_language": user_language,
        }
        with patch("forms.utils.send_email") as mock_send_answer_email:
            generate_and_queue_answer_emails(input_data=input_data)
            assert mock_generate_plotsearch_email.called
            assert mock_send_answer_email.called


# @pytest.mark.django_db
# def test_generate_area_search_pdf_and_email_to_disk(
#     answer_with_email, setup_lessor_contacts_and_service_units
# ):
#     """This test is for debugging purposes only. It generates the email and pdf files to disk."""
#     import os

#     # answer = answer_with_email.get("answer")
#     answer_id = answer_with_email.get("answer", {}).get("id")
#     with patch("forms.utils.send_email") as mock_send_answer_email:
#         input_data: AnswerInputData = {
#             "answer_id": answer_id,
#             "answer_type": AnswerType.AREA_SEARCH,
#             "user_language": "fi",
#         }
#         generate_and_queue_answer_emails(input_data=input_data)
#         email: EmailMessageInput = mock_send_answer_email.call_args_list[0].args[0]

#     directory = (
#         "/code/tmp"  # Change this to your desired path, this is for devcontainers only
#     )
#     os.makedirs(directory, exist_ok=True)
#     for i, (filename, content, mimetype) in enumerate(email.get("attachments", [])):
#         pdf_file_path = os.path.join(directory, f"{i}_{filename}")
#         with open(pdf_file_path, "wb") as f:
#             f.write(content)

#     email_file_path = os.path.join(directory, f"{email.get('to')[0]}")
#     with open(email_file_path, "w") as f:
#         f.write(email.get("subject"))
#         f.write("\n------------------------------\n\n")
#         f.write(email.get("body"))
