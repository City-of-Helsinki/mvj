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
from unittest.mock import patch

import pytest
from django.conf import settings

from utils.email import EmailMessageInput, send_email


@pytest.fixture
def email_input_fixture():
    email: EmailMessageInput = {
        "subject": "Test email",
        "body": "This is a test email",
        "from_email": settings.DEFAULT_FROM_EMAIL,
        "to": ["test@example.com"],
        "attachments": [],
    }
    return email


def test_send_answer_email(email_input_fixture: EmailMessageInput):
    with patch("django.core.mail.message.EmailMessage.send") as mock_send:
        send_email(email_input_fixture)
        assert mock_send.called


def test_send_answer_email_smtp_exceptions_not_raised(
    email_input_fixture: EmailMessageInput,
):
    """Some exceptions should not be raised, due to not being recoverable by retrying."""
    exceptions = (
        (
            SMTPRecipientsRefused,
            SMTPRecipientsRefused({"test@example.com": (550, "User unknown")}),
        ),
        (
            SMTPSenderRefused,
            SMTPSenderRefused(
                550,
                "User unknown",
                "test@example.com",
            ),
        ),
    )
    for _, side_effect in exceptions:
        with patch("django.core.mail.message.EmailMessage.send") as mock_send, patch(
            "logging.Logger.exception"
        ) as mock_logger_exception:
            mock_send.side_effect = side_effect

            send_email(email_input_fixture)

            assert mock_send.called
            assert (
                mock_logger_exception.call_count == 1
            )  # Exception should still be logged


def test_send_answer_email_smtp_exceptions_raised(
    email_input_fixture: EmailMessageInput,
):
    """Most exceptions should be raised."""
    exceptions = (
        (
            SMTPDataError,
            SMTPDataError(550, "User unknown"),
        ),
        (
            SMTPException,
            SMTPException("Error sending email"),
        ),
        (
            TimeoutError,
            TimeoutError("Connection timed out"),
        ),
        (
            SMTPServerDisconnected,
            SMTPServerDisconnected("Server disconnected"),
        ),
        (
            SMTPResponseException,
            SMTPResponseException(550, "User unknown"),
        ),
        (
            SMTPConnectError,
            SMTPConnectError(550, "Connection error"),
        ),
        (
            SMTPHeloError,
            SMTPHeloError(550, "User unknown"),
        ),
        (
            SMTPAuthenticationError,
            SMTPAuthenticationError(550, "User unknown"),
        ),
        (
            SMTPNotSupportedError,
            SMTPNotSupportedError("Not supported"),
        ),
    )
    for exception, side_effect in exceptions:
        with patch("django.core.mail.message.EmailMessage.send") as mock_send:
            with patch("logging.Logger.exception") as mock_logger_exception:
                mock_send.side_effect = side_effect

                with pytest.raises(exception):
                    send_email(email_input_fixture)

                assert mock_send.called
                assert mock_logger_exception.call_count == 1
