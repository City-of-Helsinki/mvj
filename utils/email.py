import logging
from io import BytesIO
from smtplib import (
    SMTPDataError,
    SMTPException,
    SMTPRecipientsRefused,
    SMTPSenderRefused,
)
from typing import TypedDict

from django.conf import settings
from django.core.mail import EmailMessage


class EmailMessageInput(TypedDict):
    from_email: str
    to: list[str]
    subject: str
    body: str
    attachments: list[tuple[str, bytes | BytesIO, str]]


def send_email(email_message_input: EmailMessageInput, body_is_html=False) -> None:
    """Creates an EmailMessage from the input and sends it with error handling."""
    email_message = _create_email_from_input(email_message_input, body_is_html)

    try:
        email_message.send()
    except SMTPSenderRefused:
        logging.exception(
            "Server refused sender address when sending email. Abandoning retrying."
        )
        return  # No point retrying
    except SMTPRecipientsRefused:
        logging.exception(
            "Server refused recipient address when sending email. Abandoning retrying."
        )
        return  # No point retrying
    except (SMTPDataError, SMTPException) as e:
        logging.exception(
            f"Server responded with unexpected error code when sending email: {e}"
        )
        raise e
    except TimeoutError as e:
        logging.exception("Server connection timed out when sending email.")
        raise e


def _create_email_from_input(
    email_message_input: EmailMessageInput,
    body_is_html: bool = False,
) -> EmailMessage:
    email_message = EmailMessage(**email_message_input)

    if body_is_html:
        email_message.content_subtype = "html"

    return email_message
