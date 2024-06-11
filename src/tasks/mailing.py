import smtplib

from celery import Celery
from pydantic import EmailStr

from email.message import EmailMessage
from src.settings import settings


SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465

celery = Celery("mailing_tasks", broker="redis://localhost:6379")
celery.conf.broker_connection_retry_on_startup = True


def send_email(message: EmailMessage):
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
        server.login(settings.smtp_user, settings.smtp_password)
        server.send_message(message)


def message_creator(
        subject: str,
        template: str,
        username: str,
        user_email: EmailStr,
        value: str,
) -> EmailMessage:
    """
    Creates and returns an EmailMessage object representing
    an email message that will be sent to the specified email address.

    Parameters:
    - subject (str): The subject of the message.
    - template (str): The path to the template file containing the HTML markup of the message.
    - username (str): The username to be inserted into the message template.
    - user_email (EmailStr): The email address of the recipient.
    - value (str): The value also to be inserted into the message template.

    Returns:
    - EmailMessage: An object representing the email message with configured "Subject",
    "From", and "To" fields, as well as HTML content generated based on the provided template.
    """

    email = EmailMessage()
    email["Subject"] = subject
    email["From"] = settings.smtp_user
    email["To"] = user_email

    with open(template, "r") as tmp:
        message = tmp.read().format(username, value)
    email.set_content(message, subtype="html")

    return email


@celery.task
def email_confirmation_message(username: str, email: EmailStr, code: int) -> None:
    message = message_creator(
        subject="Email confirmation",
        template="src/tasks/emailConfirmation.txt",
        username=username,
        user_email=email,
        value=code
    )
    send_email(message)


@celery.task
def two_factor_auth_message(username: str, email: EmailStr, code: int) -> None:
    message = message_creator(
        subject="2-Factor-Auth",
        template="src/tasks/2faCode.txt",
        username=username,
        user_email=email,
        value=code
    )
    send_email(message)


@celery.task
def password_recovery_message(username: str, email: EmailStr, token: str,) -> None:
    message = message_creator(
        subject="Password recover",
        template="src/tasks/passwordRecover.txt",
        username=username,
        user_email=email,
        value=token
    )
    send_email(message)

