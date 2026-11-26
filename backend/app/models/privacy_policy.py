import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import text as sql_text

from app.core.db import Base


class PrivacyPolicyVersion(Base):
    """One version of the privacy policy.

    A version starts as a draft (`published_at` is None), which admins can
    edit or discard. Publishing it makes it the active policy, numbers it
    and freezes it: published versions are never changed or deleted, so
    there is a record of every policy users agreed to. The active policy is
    the most recently published version."""

    __tablename__ = "privacy_policy_version"
    __table_args__ = (
        # At most one draft at a time.
        Index(
            "uq_privacy_policy_version_single_draft",
            sql_text("(published_at IS NULL)"),
            unique=True,
            postgresql_where=sql_text("published_at IS NULL"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    # 1, 2, 3, ... in publishing order; None while a draft.
    version: Mapped[Optional[int]] = mapped_column(unique=True)

    mode: Mapped[str] = mapped_column(default="text", server_default="text")
    text: Mapped[Optional[str]]
    url: Mapped[Optional[str]]

    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=sql_text("now()")
    )
    created_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("user.id", ondelete="SET NULL")
    )
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=sql_text("now()")
    )
    published_at: Mapped[Optional[datetime]] = mapped_column(index=True)
    published_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("user.id", ondelete="SET NULL")
    )

    created_by: Mapped[Optional["User"]] = relationship(
        lazy="selectin", foreign_keys=[created_by_id]
    )
    published_by: Mapped[Optional["User"]] = relationship(
        lazy="selectin", foreign_keys=[published_by_id]
    )

    @property
    def is_draft(self) -> bool:
        return self.published_at is None


class PrivacyPolicyConsent(Base):
    """A user agreed to a privacy policy version, and when."""

    __tablename__ = "privacy_policy_consent"
    __table_args__ = (UniqueConstraint("user_id", "policy_version_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), index=True
    )
    policy_version_id: Mapped[int] = mapped_column(
        ForeignKey("privacy_policy_version.id", ondelete="RESTRICT"), index=True
    )
    accepted_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=sql_text("now()")
    )


from app.models.user import User  # noqa: E402
