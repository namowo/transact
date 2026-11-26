"""The quality review workflow of a study (see `app.models.study_review`)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable, Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.crud.exceptions import DatabaseCommitError
from app.models.study import Study
from app.models.study_review import (
    CommentStatus,
    ReviewStatus,
    StudyReviewComment,
    StudyReviewRound,
)
from app.models.user import User
from app.schemas.study_review import ReviewProgress
from app.services.study_snapshot import diff_snapshots, take_snapshot

# Comments that still block passing the quality check.
UNRESOLVED = (CommentStatus.OPEN.value, CommentStatus.ADDRESSED.value)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _conflict(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=message)


async def _commit(db: AsyncSession) -> None:
    try:
        await db.commit()
    except SQLAlchemyError as e:
        await db.rollback()
        raise DatabaseCommitError(message=str(e))


async def list_rounds(db: AsyncSession, study_id: UUID) -> list[StudyReviewRound]:
    result = await db.execute(
        select(StudyReviewRound)
        .where(StudyReviewRound.study_id == study_id)
        .order_by(StudyReviewRound.number)
        .execution_options(populate_existing=True)
    )
    return list(result.scalars().all())


async def latest_round(db: AsyncSession, study_id: UUID) -> Optional[StudyReviewRound]:
    rounds = await list_rounds(db, study_id)
    return rounds[-1] if rounds else None


async def list_comments(db: AsyncSession, study_id: UUID) -> list[StudyReviewComment]:
    """Top-level comments, oldest first, with their replies."""
    result = await db.execute(
        select(StudyReviewComment)
        .where(StudyReviewComment.study_id == study_id, StudyReviewComment.parent_id.is_(None))
        .order_by(StudyReviewComment.created_at)
        # Self-referential, so the relationship's own eager loading stops
        # at the first level.
        .options(selectinload(StudyReviewComment.replies))
        .execution_options(populate_existing=True)
    )
    return list(result.scalars().all())


def progress_of(statuses: Iterable[Optional[str]]) -> ReviewProgress:
    progress = ReviewProgress()
    for value in statuses:
        if value not in (s.value for s in CommentStatus):
            continue
        progress.total += 1
        setattr(progress, value, getattr(progress, value) + 1)
    return progress


async def progress_by_study(db: AsyncSession, study_ids: list[UUID]) -> dict[UUID, ReviewProgress]:
    if not study_ids:
        return {}
    result = await db.execute(
        select(StudyReviewComment.study_id, StudyReviewComment.status, func.count())
        .where(
            StudyReviewComment.study_id.in_(study_ids),
            StudyReviewComment.parent_id.is_(None),
        )
        .group_by(StudyReviewComment.study_id, StudyReviewComment.status)
    )
    statuses: dict[UUID, list[str]] = {study_id: [] for study_id in study_ids}
    for study_id, value, count in result.all():
        statuses[study_id].extend([value] * count)
    return {study_id: progress_of(values) for study_id, values in statuses.items()}


async def get_comment(db: AsyncSession, study_id: UUID, comment_id: UUID) -> StudyReviewComment:
    comment = await db.get(StudyReviewComment, comment_id)
    if comment is None or comment.study_id != study_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Comment not found.")
    return comment


# --- Workflow ---------------------------------------------------------------


async def submit(db: AsyncSession, study: Study, user: User) -> StudyReviewRound:
    """Open the next review round with a snapshot of the study's data."""
    if study.review_status not in (ReviewStatus.DRAFT.value, ReviewStatus.CHANGES_REQUESTED.value):
        raise _conflict("This study can't be submitted for quality check right now.")
    previous = await latest_round(db, study.id)
    snapshot = await take_snapshot(db, study.id)
    round_ = StudyReviewRound(
        study_id=study.id,
        number=(previous.number if previous else 0) + 1,
        submitted_by_id=user.id,
        snapshot=snapshot,
    )
    db.add(round_)
    study.review_status = ReviewStatus.IN_REVIEW.value
    await _commit(db)
    return round_


async def _decide(db: AsyncSession, study: Study, user: User, decision: str) -> None:
    current = await latest_round(db, study.id)
    if current is not None and current.decision is None:
        current.decision = decision
        current.decided_at = _now()
        current.decided_by_id = user.id


async def request_changes(db: AsyncSession, study: Study, user: User) -> None:
    if study.review_status != ReviewStatus.IN_REVIEW.value:
        raise _conflict("Only studies in review can be sent back for changes.")
    await _decide(db, study, user, ReviewStatus.CHANGES_REQUESTED.value)
    study.review_status = ReviewStatus.CHANGES_REQUESTED.value
    await _commit(db)


async def assert_can_pass(db: AsyncSession, study: Study) -> None:
    unresolved = await db.scalar(
        select(func.count())
        .select_from(StudyReviewComment)
        .where(
            StudyReviewComment.study_id == study.id,
            StudyReviewComment.parent_id.is_(None),
            StudyReviewComment.status.in_(UNRESOLVED),
        )
    )
    if unresolved:
        raise _conflict(
            f"Resolve all review comments before passing the quality check ({unresolved} still open)."
        )


async def mark_passed(db: AsyncSession, study: Study, user: User) -> None:
    """Close the open round as passed. Committed by the caller."""
    await _decide(db, study, user, ReviewStatus.PASSED.value)
    study.review_status = ReviewStatus.PASSED.value


# --- Comments ---------------------------------------------------------------


async def add_comment(
    db: AsyncSession,
    study: Study,
    user: User,
    *,
    body: str,
    section: str,
    target_id: Optional[str],
    target_label: Optional[str],
    field_label: Optional[str],
) -> StudyReviewComment:
    current = await latest_round(db, study.id)
    comment = StudyReviewComment(
        study_id=study.id,
        round_number=current.number if current else None,
        section=section,
        target_id=target_id,
        target_label=target_label if target_id else None,
        field_label=field_label if target_id else None,
        body=body.strip(),
        status=CommentStatus.OPEN.value,
        author_id=user.id,
    )
    db.add(comment)
    await _commit(db)
    return comment


async def add_reply(
    db: AsyncSession, parent: StudyReviewComment, user: User, body: str
) -> StudyReviewComment:
    reply = StudyReviewComment(
        study_id=parent.study_id,
        parent_id=parent.id,
        round_number=parent.round_number,
        section=parent.section,
        body=body.strip(),
        author_id=user.id,
    )
    db.add(reply)
    await _commit(db)
    return reply


async def update_comment(
    db: AsyncSession,
    comment: StudyReviewComment,
    user: User,
    *,
    body: Optional[str],
    new_status: Optional[str],
    can_review: bool,
    can_respond: bool,
) -> None:
    if body is not None and body.strip() != comment.body:
        if comment.author_id != user.id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "You can only edit your own comments.")
        comment.body = body.strip()
        comment.edited_at = _now()
    if new_status is not None and new_status != comment.status:
        if comment.parent_id is not None:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Replies have no status.")
        # The laboratory marks comments addressed (or takes that back);
        # resolving and reopening resolved comments is up to quality checkers.
        lab_move = {comment.status, new_status} == {
            CommentStatus.OPEN.value,
            CommentStatus.ADDRESSED.value,
        }
        if not (can_review or (can_respond and lab_move)):
            raise HTTPException(
                status.HTTP_403_FORBIDDEN, "You can't change the status of this comment."
            )
        comment.status = new_status
        comment.status_changed_at = _now()
        comment.status_changed_by_id = user.id
    await _commit(db)


async def delete_comment(db: AsyncSession, comment: StudyReviewComment, user: User) -> None:
    if comment.author_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You can only delete your own comments.")
    await db.delete(comment)
    await _commit(db)


# --- Diff -------------------------------------------------------------------


async def _snapshot_of(db: AsyncSession, study_id: UUID, number: int) -> dict:
    snapshot = await db.scalar(
        select(StudyReviewRound.snapshot).where(
            StudyReviewRound.study_id == study_id, StudyReviewRound.number == number
        )
    )
    if snapshot is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Review round not found.")
    return snapshot


async def diff(
    db: AsyncSession, study_id: UUID, from_round: int, to_round: Optional[int]
) -> list[dict]:
    """What changed from round `from_round`'s snapshot to round `to_round`'s
    (or to the current data when `to_round` is None)."""
    old = await _snapshot_of(db, study_id, from_round)
    new = (
        await _snapshot_of(db, study_id, to_round)
        if to_round is not None
        else await take_snapshot(db, study_id)
    )
    return diff_snapshots(old, new)
