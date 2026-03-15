from pydantic import EmailStr
from jinja2 import Environment, FileSystemLoader

# Code snippets are only available for the latest version. Current version is 1.x

from msgraph.generated.users.item.send_mail.send_mail_post_request_body import (
    SendMailPostRequestBody,
)
from msgraph.generated.models.message import Message
from msgraph.generated.models.item_body import ItemBody
from msgraph.generated.models.body_type import BodyType
from msgraph.generated.models.recipient import Recipient
from msgraph.generated.models.email_address import EmailAddress
from os import path

from .msgraph_config import graph_client
from app.core.config import settings


def get_content(template_name: str, template_values: dict) -> str:
    current_path = path.dirname(path.abspath(__file__))
    # Set the path to the templates folder inside the current directory
    template_path = path.join(current_path, "templates")
    templateLoader = FileSystemLoader(searchpath=template_path)
    templateEnv = Environment(loader=templateLoader)
    template = templateEnv.get_template(template_name)
    return template.render(template_values)


async def send_mail(
    subject: str, to_recipient: EmailStr, template_name: str, template_values: dict
):

    request_body = SendMailPostRequestBody(
        message=Message(
            subject=subject,
            body=ItemBody(
                content_type=BodyType.Html,
                content=get_content(template_name, template_values),
            ),
            to_recipients=[
                Recipient(
                    email_address=EmailAddress(
                        address=to_recipient,
                    ),
                ),
            ],
        ),
        save_to_sent_items=False,
    )

    user_id = settings.GRAPH_API_USER_ID  # Replace with the user's ID or email
    await graph_client.users.by_user_id(user_id).send_mail.post(request_body)
