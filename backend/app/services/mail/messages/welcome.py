import logging

from app.services.mail import send_mail

logger = logging.getLogger(__name__)


async def send_welcome_mail(user):
    user_dict = {"first_name": user.first_name, "last_name": user.last_name}

    try:
        await send_mail(
            subject="Welcome to the TransAct Repository",
            to_recipient=user.email,
            template_name="welcome-user.html",
            template_values=user_dict,
        )
    except Exception:
        logger.exception("Error sending welcome email to %s", user.email)
