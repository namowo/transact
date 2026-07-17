import logging
from email.message import EmailMessage
from os import path

import aiosmtplib
from jinja2 import Environment, FileSystemLoader
from pydantic import EmailStr

from app.core.config import settings

logger = logging.getLogger(__name__)


def get_content(template_name: str, template_values: dict) -> str:
    current_path = path.dirname(path.abspath(__file__))
    template_path = path.join(current_path, "templates")
    template_loader = FileSystemLoader(searchpath=template_path)
    template_env = Environment(loader=template_loader)
    template = template_env.get_template(template_name)
    return template.render(template_values)


async def send_mail(
    subject: str, to_recipient: EmailStr, template_name: str, template_values: dict
):
    body = get_content(template_name, template_values)

    if not settings.SMTP_HOST:
        # print(), not logger.info(): guaranteed visible regardless of the
        # app's logging configuration, since this is a dev-only convenience.
        print(
            f"SMTP not configured - logging email instead of sending.\n"
            f"To: {to_recipient}\nSubject: {subject}\n\n{body}"
        )
        return

    message = EmailMessage()
    message["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
    message["To"] = to_recipient
    message["Subject"] = subject
    message.set_content(body, subtype="html")

    await aiosmtplib.send(
        message,
        hostname=settings.SMTP_HOST,
        port=settings.SMTP_PORT,
        username=settings.SMTP_USERNAME,
        password=settings.SMTP_PASSWORD,
        start_tls=settings.SMTP_USE_TLS,
    )
