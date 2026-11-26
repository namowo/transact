"""The quality review of a study.

A laboratory submits a study for review, which opens a *round* and freezes a
snapshot of the study's data (see `app.services.study_snapshot`). Quality
checkers leave *comments* - on the study as a whole, on one of its sections
or on a single record - and either request changes, which hands the study
back to the laboratory, or pass it. Resubmitting opens the next round, so
checkers can compare snapshots to see what the laboratory changed.

Top-level comments track the demanded changes: the laboratory marks them
addressed, a quality checker resolves them (or reopens them). Replies carry
the discussion and have no status of their own.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Text, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, deferred, mapped_column, relationship

from app.core.db import Base


class ReviewStatus(str, Enum):
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    CHANGES_REQUESTED = "changes_requested"
    PASSED = "passed"


class CommentStatus(str, Enum):
    OPEN = "open"
    ADDRESSED = "addressed"
    RESOLVED = "resolved"


class StudyReviewRound(Base):
    __tablename__ = "study_review_round"
    __table_args__ = (UniqueConstraint("study_id", "number"),)

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    study_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("study.id", ondelete="CASCADE"), index=True
    )
    # 1, 2, ... per study.
    number: Mapped[int]
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    submitted_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("user.id", ondelete="SET NULL")
    )
    submitted_by: Mapped[Optional["User"]] = relationship(
        lazy="selectin", foreign_keys=[submitted_by_id]
    )
    # "changes_requested" or "passed"; None while the round is open.
    decision: Mapped[Optional[str]]
    decided_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    decided_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("user.id", ondelete="SET NULL")
    )
    decided_by: Mapped[Optional["User"]] = relationship(
        lazy="selectin", foreign_keys=[decided_by_id]
    )
    # The study's data when it was submitted. Large - only loaded for diffs.
    snapshot: Mapped[dict] = deferred(
        mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    )


class StudyReviewComment(Base):
    __tablename__ = "study_review_comment"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    study_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("study.id", ondelete="CASCADE"), index=True
    )
    # Replies point at their top-level comment.
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("study_review_comment.id", ondelete="CASCADE"),
        index=True,
    )
    # The review round the comment was made in (None before the first).
    round_number: Mapped[Optional[int]]
    # What the comment is about: "general" or a snapshot section key
    # (app.services.study_snapshot.SECTIONS), optionally narrowed to one
    # record (its id and a label to show) and one of its fields.
    section: Mapped[str] = mapped_column(server_default="general")
    target_id: Mapped[Optional[str]]
    target_label: Mapped[Optional[str]]
    field_label: Mapped[Optional[str]]
    body: Mapped[str] = mapped_column(Text)
    # Top-level comments only.
    status: Mapped[Optional[str]]
    author_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("user.id", ondelete="SET NULL")
    )
    author: Mapped[Optional["User"]] = relationship(lazy="selectin", foreign_keys=[author_id])
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    edited_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    status_changed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    status_changed_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("user.id", ondelete="SET NULL")
    )
    status_changed_by: Mapped[Optional["User"]] = relationship(
        lazy="selectin", foreign_keys=[status_changed_by_id]
    )
    replies: Mapped[list["StudyReviewComment"]] = relationship(
        lazy="selectin",
        cascade="all, delete-orphan",
        order_by="StudyReviewComment.created_at",
    )


from app.models.user import User
