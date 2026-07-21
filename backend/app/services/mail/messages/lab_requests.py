import logging

from app.services.mail import send_mail

logger = logging.getLogger(__name__)


async def send_new_lab_requested_mail(superuser, laboratory, requester):
    try:
        await send_mail(
            subject="New laboratory request awaiting approval",
            to_recipient=superuser.email,
            template_name="new-lab-requested.html",
            template_values={
                "first_name": superuser.first_name,
                "laboratory_name": laboratory.laboratory_name,
                "requester_first_name": requester.first_name,
                "requester_last_name": requester.last_name,
                "requester_email": requester.email,
            },
        )
    except Exception:
        logger.exception(
            "Error sending new-lab-requested email to %s", superuser.email
        )


async def send_lab_approved_mail(user, laboratory):
    try:
        await send_mail(
            subject="Your laboratory has been approved",
            to_recipient=user.email,
            template_name="lab-approved.html",
            template_values={
                "first_name": user.first_name,
                "laboratory_name": laboratory.laboratory_name,
            },
        )
    except Exception:
        logger.exception("Error sending lab-approved email to %s", user.email)


async def send_lab_denied_mail(user, laboratory):
    try:
        await send_mail(
            subject="Your laboratory request was not approved",
            to_recipient=user.email,
            template_name="lab-denied.html",
            template_values={
                "first_name": user.first_name,
                "laboratory_name": laboratory.laboratory_name,
            },
        )
    except Exception:
        logger.exception("Error sending lab-denied email to %s", user.email)
