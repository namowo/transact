import logging

from app.services.mail import send_mail
from app.utils.url import create_token_url

logger = logging.getLogger(__name__)


async def send_verification_mail(user, token: str):
    url = create_token_url("verify-email", token)

    user_dict = {"first_name": user.first_name, "last_name": user.last_name, "url": url}

    try:
        await send_mail(
            subject="Confirm your TransAct account",
            to_recipient=user.email,
            template_name="verify-account.html",
            template_values=user_dict,
        )
    except Exception:
        logger.exception("Error sending verification email to %s", user.email)
