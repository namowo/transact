"""The notifications a user can receive, and through which channels.

Each type is tied to the permission that makes it relevant: a user is only
offered - and only receives - notifications their permissions allow, so
changing someone's groups changes their notifications too. Choices are
stored per user (`User.notification_settings`); types or channels the user
never touched fall back to the defaults here.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Literal

from app.core.permission_catalog import Permission

Channel = Literal["email", "browser"]
CHANNELS: tuple[Channel, ...] = ("email", "browser")


class NotificationType(str, Enum):
    LAB_MEMBERSHIP_REQUEST = "lab_membership_request"
    LABORATORY_REQUEST = "laboratory_request"
    STUDY_QUALITY_CHECKED = "study_quality_checked"
    STUDY_CHANGES_REQUESTED = "study_changes_requested"
    STUDY_SUBMITTED_FOR_REVIEW = "study_submitted_for_review"


@dataclass(frozen=True)
class NotificationTypeInfo:
    key: NotificationType
    label: str
    description: str
    permission: Permission
    # Channels this type can be delivered through, with their defaults.
    defaults: dict[Channel, bool]


NOTIFICATION_TYPES: tuple[NotificationTypeInfo, ...] = (
    NotificationTypeInfo(
        NotificationType.LAB_MEMBERSHIP_REQUEST,
        "Membership requests",
        "Someone asks to join your laboratory.",
        Permission.MANAGE_LAB_MEMBERS,
        {"email": True, "browser": False},
    ),
    NotificationTypeInfo(
        NotificationType.LABORATORY_REQUEST,
        "New laboratory requests",
        "Someone asks to create a new laboratory that needs approval.",
        Permission.MANAGE_LABORATORIES,
        {"email": True, "browser": False},
    ),
    NotificationTypeInfo(
        NotificationType.STUDY_QUALITY_CHECKED,
        "Study passed quality check",
        "One of your laboratory's studies passed its quality check and was published.",
        Permission.ENTER_DATA,
        {"email": True},
    ),
    NotificationTypeInfo(
        NotificationType.STUDY_CHANGES_REQUESTED,
        "Changes requested on a study",
        "A quality checker asks for changes to one of your laboratory's studies.",
        Permission.ENTER_DATA,
        {"email": True},
    ),
    NotificationTypeInfo(
        NotificationType.STUDY_SUBMITTED_FOR_REVIEW,
        "Study submitted for quality check",
        "A laboratory submits a study for quality check, or resubmits it after changes.",
        Permission.QUALITY_CHECK,
        {"email": True},
    ),
)

NOTIFICATION_TYPE_INFO: dict[NotificationType, NotificationTypeInfo] = {
    t.key: t for t in NOTIFICATION_TYPES
}
