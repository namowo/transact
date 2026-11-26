from .welcome import send_welcome_mail
from .reset_password import send_reset_password_mail
from .verification import send_verification_mail
from .lab_requests import (
    send_new_lab_requested_mail,
    send_lab_approved_mail,
    send_lab_denied_mail,
)
from .lab_membership import (
    send_new_membership_request_mail,
    send_membership_approved_mail,
    send_membership_denied_mail,
)
from .invitation import send_invitation_mail
from .study_quality_check import (
    send_study_changes_requested_mail,
    send_study_quality_checked_mail,
    send_study_submitted_for_review_mail,
)
from .privacy_policy import send_privacy_policy_updated_mails
