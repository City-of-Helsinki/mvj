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


def send_email(email_message_input: EmailMessageInput) -> None:
    if hasattr(settings, "DEBUG") and settings.DEBUG is True:
        logging.info("Not sending email in debug mode.")
        logging.info(f"Email message: {email_message_input}")
        return

    email_message = EmailMessage(**email_message_input)

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
