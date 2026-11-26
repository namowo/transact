import logging

from app.core.config import settings
from app.services.mail import send_mail
from app.utils.url import create_token_url

logger = logging.getLogger(__name__)


async def send_invitation_mail(user, inviter, token: str):
    url = create_token_url("accept-invitation", token)

    try:
        await send_mail(
            subject="You're invited to the TransAct Repository",
            to_recipient=user.email,
            template_name="invitation.html",
            template_values={
                "first_name": user.first_name,
                "last_name": user.last_name,
                "inviter_first_name": inviter.first_name,
                "inviter_last_name": inviter.last_name,
                "laboratory_name": (
                    user.laboratory.laboratory_name if user.laboratory else None
                ),
                "expire_days": max(1, settings.INVITATION_TOKEN_EXPIRE_HOURS // 24),
                "url": url,
            },
        )
    except Exception:
        logger.exception("Error sending invitation email to %s", user.email)
