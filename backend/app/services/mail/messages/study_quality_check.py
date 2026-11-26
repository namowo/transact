import logging

from app.core.config import settings
from app.core.notification_catalog import NotificationType
from app.services.mail import send_mail

logger = logging.getLogger(__name__)


async def send_study_quality_checked_mail(user, study):
    if not user.wants_notification(NotificationType.STUDY_QUALITY_CHECKED, "email"):
        return
    try:
        await send_mail(
            subject="Your study passed its quality check",
            to_recipient=user.email,
            template_name="study-quality-checked.html",
            template_values={
                "first_name": user.first_name,
                "study_title": study.title,
                "url": f"{settings.FRONTEND_URL}/studies/laboratory",
            },
        )
    except Exception:
        logger.exception("Error sending study-quality-checked email to %s", user.email)


async def send_study_changes_requested_mail(user, study, open_comments: int):
    if not user.wants_notification(NotificationType.STUDY_CHANGES_REQUESTED, "email"):
        return
    try:
        await send_mail(
            subject="Changes requested on your study",
            to_recipient=user.email,
            template_name="study-changes-requested.html",
            template_values={
                "first_name": user.first_name,
                "study_title": study.title,
                "open_comments": open_comments,
                "url": f"{settings.FRONTEND_URL}/studies/{study.id}/edit?review=1",
            },
        )
    except Exception:
        logger.exception("Error sending study-changes-requested email to %s", user.email)


async def send_study_submitted_for_review_mail(user, study, round_number: int):
    if not user.wants_notification(NotificationType.STUDY_SUBMITTED_FOR_REVIEW, "email"):
        return
    try:
        await send_mail(
            subject=(
                "A study was submitted for quality check"
                if round_number == 1
                else "A study was resubmitted for quality check"
            ),
            to_recipient=user.email,
            template_name="study-submitted-for-review.html",
            template_values={
                "first_name": user.first_name,
                "study_title": study.title,
                "laboratory_name": study.laboratory.laboratory_name if study.laboratory else None,
                "round_number": round_number,
                "url": f"{settings.FRONTEND_URL}/studies/{study.id}/edit?review=1",
            },
        )
    except Exception:
        logger.exception("Error sending study-submitted-for-review email to %s", user.email)
