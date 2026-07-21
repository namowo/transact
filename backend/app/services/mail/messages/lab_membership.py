import logging

from app.services.mail import send_mail

logger = logging.getLogger(__name__)


async def send_new_membership_request_mail(lab_admin, requester, laboratory):
    try:
        await send_mail(
            subject="New laboratory membership request",
            to_recipient=lab_admin.email,
            template_name="new-membership-request.html",
            template_values={
                "first_name": lab_admin.first_name,
                "laboratory_name": laboratory.laboratory_name,
                "requester_first_name": requester.first_name,
                "requester_last_name": requester.last_name,
                "requester_email": requester.email,
            },
        )
    except Exception:
        logger.exception(
            "Error sending new-membership-request email to %s", lab_admin.email
        )


async def send_membership_approved_mail(user, laboratory):
    try:
        await send_mail(
            subject="Your laboratory membership request was approved",
            to_recipient=user.email,
            template_name="membership-approved.html",
            template_values={
                "first_name": user.first_name,
                "laboratory_name": laboratory.laboratory_name,
            },
        )
    except Exception:
        logger.exception("Error sending membership-approved email to %s", user.email)


async def send_membership_denied_mail(user, laboratory):
    try:
        await send_mail(
            subject="Your laboratory membership request was not approved",
            to_recipient=user.email,
            template_name="membership-denied.html",
            template_values={
                "first_name": user.first_name,
                "laboratory_name": laboratory.laboratory_name,
            },
        )
    except Exception:
        logger.exception("Error sending membership-denied email to %s", user.email)
