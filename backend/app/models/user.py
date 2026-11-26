import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import text

from app.core.db import Base


class User(Base):
    __tablename__ = "user"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, index=True, server_default=text("gen_random_uuid()")
    )
    email: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)
    hashed_password: Mapped[str]
    first_name: Mapped[str]
    last_name: Mapped[str]
    is_active: Mapped[bool] = mapped_column(nullable=False, server_default=text("true"))
    is_verified: Mapped[bool] = mapped_column(
        nullable=False, server_default=text("false")
    )
    # Set while an invited user hasn't accepted their invitation yet; their
    # password is a random one nobody knows until then.
    invitation_pending: Mapped[bool] = mapped_column(
        nullable=False, server_default=text("false")
    )
    passkey_prompt_dismissed: Mapped[bool] = mapped_column(
        nullable=False, server_default=text("false")
    )

    # --- Two-factor authentication ------------------------------------------
    # Authenticator app (TOTP) secret, set once the user confirmed a code.
    # Encrypted, see app.core.encryption.
    totp_secret: Mapped[Optional[str]]
    # Secret shown during setup, until the user confirms a code from it.
    # Encrypted too.
    totp_pending_secret: Mapped[Optional[str]]
    # Time step of the last accepted code, so it can't be used again.
    totp_last_used_step: Mapped[Optional[int]] = mapped_column(BigInteger)
    # SHA-256 hashes of the unused recovery codes.
    totp_recovery_codes: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    # Wrong codes in a row; too many lock the code step for a while.
    totp_failed_attempts: Mapped[int] = mapped_column(
        nullable=False, server_default=text("0")
    )
    totp_locked_until: Mapped[Optional[datetime]]

    # --- Sign-in lockout ------------------------------------------------------
    # Wrong passwords in a row; reaching MAX_FAILED_LOGIN_ATTEMPTS locks the
    # account until an admin unlocks it.
    failed_login_attempts: Mapped[int] = mapped_column(
        nullable=False, server_default=text("0")
    )
    locked_at: Mapped[Optional[datetime]]

    # Interactive guides (e.g. "onboarding", "new-study") the user has
    # finished or skipped, so they aren't started automatically again.
    completed_tours: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )

    # Per notification type and channel ({"lab_membership_request":
    # {"email": true, "browser": false}, ...}); anything missing uses the
    # default from app.core.notification_catalog. Use `wants_notification`.
    notification_settings: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )

    # BCP 47 language tag (e.g. "en-US", "de-DE"); decides how numbers are
    # typed and shown, e.g. the decimal separator.
    locale: Mapped[str] = mapped_column(
        nullable=False, server_default=text("'en-US'")
    )

    # The user's saved column sort per data table ({"samples": [{"field",
    # "order"}, ...]}); CSV exports follow it too. Missing tables use the app
    # default.
    table_sorts: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    laboratory_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("laboratory.id", ondelete="RESTRICT")
    )
    laboratory: Mapped[Optional["Laboratory"]] = relationship(
        lazy="selectin", foreign_keys=[laboratory_id]
    )

    groups: Mapped[list["UserGroup"]] = relationship(
        secondary="user_group_member", lazy="selectin", order_by="UserGroup.name"
    )

    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=text("now()")
    )

    # Every privacy policy version the user agreed to.
    privacy_policy_consents: Mapped[list["PrivacyPolicyConsent"]] = relationship(
        lazy="selectin", cascade="all, delete-orphan", passive_deletes=True
    )

    # Not stored: set on the signed-in user when their session may only set
    # up a second factor (see app.core.deps).
    two_factor_setup_required = False

    @property
    def accepted_privacy_policy_ids(self) -> list[int]:
        return sorted(c.policy_version_id for c in self.privacy_policy_consents)

    @property
    def is_locked(self) -> bool:
        return self.locked_at is not None

    @property
    def totp_enabled(self) -> bool:
        return self.totp_secret is not None

    @property
    def recovery_codes_remaining(self) -> int:
        return len(self.totp_recovery_codes or [])

    # --- Notifications ------------------------------------------------------

    @property
    def resolved_notification_settings(self) -> dict[str, dict[str, bool]]:
        """Every type's channels, stored choices over the defaults."""
        stored = self.notification_settings or {}
        return {
            info.key.value: {
                channel: bool(stored.get(info.key.value, {}).get(channel, default))
                for channel, default in info.defaults.items()
            }
            for info in NOTIFICATION_TYPES
        }

    def can_receive_notification(self, type: "NotificationType") -> bool:
        return self.can(NOTIFICATION_TYPE_INFO[type].permission)

    def wants_notification(self, type: "NotificationType", channel: "Channel") -> bool:
        """Whether to notify the user: they hold the type's permission, the
        type supports the channel, and they haven't turned it off."""
        return self.can_receive_notification(type) and self.resolved_notification_settings[
            type.value
        ].get(channel, False)

    # --- Permissions --------------------------------------------------------

    @property
    def permissions(self) -> frozenset[str]:
        """Everything the user's groups grant (see app.core.permission_catalog).

        Laboratory-scoped permissions only apply to the user's own
        laboratory; use `can_in_laboratory` for those."""
        return frozenset(
            permission for group in self.groups for permission in group.permissions
        )

    def can(self, permission: "Permission") -> bool:
        return permission.value in self.permissions

    def can_in_laboratory(
        self, permission: "Permission", laboratory_id: Optional[uuid.UUID]
    ) -> bool:
        return (
            laboratory_id is not None
            and self.laboratory_id == laboratory_id
            and self.can(permission)
        )


from app.core.notification_catalog import (  # noqa: E402
    NOTIFICATION_TYPE_INFO,
    NOTIFICATION_TYPES,
    Channel,
    NotificationType,
)
from app.core.permission_catalog import Permission  # noqa: E402
from app.models.laboratory import Laboratory  # noqa: E402
from app.models.privacy_policy import PrivacyPolicyConsent  # noqa: E402
from app.models.user_group import UserGroup  # noqa: E402
