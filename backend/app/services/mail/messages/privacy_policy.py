import logging

from app.core.config import settings
from app.services.mail import send_mail

logger = logging.getLogger(__name__)


async def send_privacy_policy_updated_mails(recipients: list[tuple[str, str, str]]):
    """Tell users the privacy policy changed. `recipients` are (email,
    first name, last name), so this can run after the request's database
    session is gone."""
    url = f"{settings.FRONTEND_URL.rstrip('/')}/privacy-policy"
    for email, first_name, last_name in recipients:
        try:
            await send_mail(
                subject="We updated our privacy policy",
                to_recipient=email,
                template_name="privacy-policy-updated.html",
                template_values={
                    "first_name": first_name,
                    "last_name": last_name,
                    "url": url,
                },
            )
        except Exception:
            logger.exception("Error sending privacy-policy-updated email to %s", email)
