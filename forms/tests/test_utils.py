from smtplib import (
    SMTPAuthenticationError,
    SMTPConnectError,
    SMTPDataError,
    SMTPException,
    SMTPHeloError,
    SMTPNotSupportedError,
    SMTPRecipientsRefused,
    SMTPResponseException,
    SMTPSenderRefused,
    SMTPServerDisconnected,
)
from typing import Any, Iterator
from unittest.mock import patch

import pytest
from django.conf import settings
from django.core.mail.message import EmailMessage

from forms.enums import AnswerType
from forms.models import Field, FieldType, Section
from forms.utils import (
    AnswerInputData,
    clone_object,
    generate_and_queue_answer_emails,
    send_answer_email,
)


@pytest.mark.django_db
def test_form_cloning(basic_template_form):
    section_count = Section.objects.all().count()
    field_count = Field.objects.all().count()
    fieldtype_count = FieldType.objects.all().count()

    new_form = clone_object(basic_template_form)

    new_section_count = Section.objects.all().count()
    new_field_count = Field.objects.all().count()
    new_fieldtype_count = FieldType.objects.all().count()

    assert new_form.id != basic_template_form
    assert new_section_count == section_count * 2
    assert new_field_count == field_count * 2
    assert new_fieldtype_count == fieldtype_count


@pytest.mark.django_db
def test_generate_and_queue_answer_emails(answer_with_email):
    answer = answer_with_email.get("answer")

    with patch("forms.utils.async_task") as mock_async_task:

        input_data: AnswerInputData = {
            "answer_id": answer.get("id"),
            "answer_type": AnswerType.AREA_SEARCH,
        }
        generate_and_queue_answer_emails(input_data=input_data)

        assert mock_async_task.called
        call_function, email_message = mock_async_task.call_args.args
        assert call_function.__name__ == "send_answer_email"
        email: EmailMessage = email_message
        assert email.from_email == settings.DEFAULT_FROM_EMAIL
        assert (
            "Kulttuuri ja vapaa-aika" in email.body
            or "Culture and leisure" in email.body
        ), "Email body should contain mapped lessor name"
        assert (
            "Tarkempi kuvaus käyttötarkoituksesta: Want to hold Helsinki Olympics 2028 here"
            in email.body
            or "Description intended use: Want to hold Helsinki Olympics 2028 here"
            in email.body
        )

        def _find_keys_in_dict(dictionary: dict, key_to_find: str) -> Iterator[Any]:
            """Finds all instances of key_to_find from a dictionary recursively"""
            for key, value in dictionary.items():
                if key == key_to_find:
                    yield value
                if isinstance(value, dict):
                    yield from _find_keys_in_dict(value, key_to_find)

        emails_form_fields = list(
            _find_keys_in_dict(answer.get("entries_data"), "sahkoposti")
        )
        emails_to = list(set([obj.get("value") for obj in emails_form_fields]))

        for email_address in email.to:
            assert email_address in emails_to
        assert mock_async_task.call_count == len(emails_to)


# def test_generate_area_search_pdf_and_email_to_disk(answer_with_email):
#     """This test is for debugging purposes only. It generates the email and pdf files to disk."""
#     import os
#     answer = answer_with_email.get("answer")
#     with patch("forms.utils.async_task") as mock_async_task:
#         generate_and_queue_answer_emails(answer.get("id"))
#         _, kwargs = mock_async_task.call_args
#         data = kwargs.get("input_data")
#         email: EmailMessage = data.get("email_message")

#     directory = "/code/tmp" # Change this to your desired path, this is for devcontainers only
#     os.makedirs(directory, exist_ok=True)
#     for i, (filename, content, mimetype) in enumerate(email.attachments):
#         pdf_file_path = os.path.join(directory, f"{i}_{filename}")
#         with open(pdf_file_path, "wb") as f:
#             f.write(content)

#     email_file_path = os.path.join(directory, f"{email.to[0]}")
#     with open(email_file_path, "wb") as f:
#         f.write(email.body.encode("utf-8"))


def test_send_answer_email(answer_email_message: EmailMessage):
    with patch("django.core.mail.message.EmailMessage.send") as mock_send:
        send_answer_email(answer_email_message)
        assert mock_send.called


def test_send_answer_email_debug(answer_email_message: EmailMessage):
    with patch("django.core.mail.message.EmailMessage.send") as mock_send:
        with patch("logging.info") as mock_logging:
            settings.DEBUG = True
            send_answer_email(answer_email_message)
            assert not mock_send.called
            assert mock_logging.call_count == 2


def test_send_answer_email_smtp_exceptions_not_raised(
    answer_email_message: EmailMessage,
):
    exceptions = (
        (
            SMTPRecipientsRefused,
            SMTPRecipientsRefused({"test@example.com": (550, "User unknown")}),
        ),
        (
            SMTPSenderRefused,
            SMTPSenderRefused(550, "User unknown", "test@example.com",),
        ),
    )
    for _, side_effect in exceptions:
        with patch("django.core.mail.message.EmailMessage.send") as mock_send:
            with patch("logging.exception") as mock_logging:
                settings.DEBUG = False
                mock_send.side_effect = side_effect
                send_answer_email(answer_email_message)
                assert mock_send.called
                assert mock_logging.call_count == 1


def test_send_answer_email_smtp_exceptions_raised(answer_email_message: EmailMessage):
    exceptions = (
        (SMTPDataError, SMTPDataError(550, "User unknown"),),
        (SMTPException, SMTPException("Error sending email"),),
        (TimeoutError, TimeoutError("Connection timed out"),),
        (SMTPServerDisconnected, SMTPServerDisconnected("Server disconnected"),),
        (SMTPResponseException, SMTPResponseException(550, "User unknown"),),
        (SMTPConnectError, SMTPConnectError(550, "Connection error"),),
        (SMTPHeloError, SMTPHeloError(550, "User unknown"),),
        (SMTPAuthenticationError, SMTPAuthenticationError(550, "User unknown"),),
        (SMTPNotSupportedError, SMTPNotSupportedError("Not supported"),),
    )
    for exception, side_effect in exceptions:
        with patch("django.core.mail.message.EmailMessage.send") as mock_send:
            with patch("logging.exception") as mock_logging:
                settings.DEBUG = False
                mock_send.side_effect = side_effect
                with pytest.raises(exception):
                    send_answer_email(answer_email_message)
                assert mock_send.called
                assert mock_logging.call_count == 1
