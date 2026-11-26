"""Quality review of studies: review rounds, comments and diffs.

See `app.models.study_review` for the workflow."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import current_active_user, current_quality_checker, get_async_session
from app.core.permissions import (
    assert_can_edit_study,
    can_edit_study,
    can_review_study,
    can_view_study,
)
from app.crud.study import crud_study
from app.crud.user import crud_user
from app.models.study import Study
from app.models.study_review import ReviewStatus
from app.models.user import User
from app.schemas.study_review import (
    CommentCreate,
    CommentUpdate,
    ReplyCreate,
    ReviewQueueEntry,
    ReviewSection,
    StudyReviewDiff,
    StudyReviewRead,
    StudyReviewRecords,
)
from app.services import study_review as review
from app.services.mail.messages import (
    send_study_changes_requested_mail,
    send_study_submitted_for_review_mail,
)
from app.services.study_snapshot import (
    COMMENT_SECTIONS,
    SECTION_KEYS,
    snapshot_records,
    take_snapshot,
)

router = APIRouter()


async def _study(db: AsyncSession, id: UUID, user: User) -> Study:
    study = await crud_study.get(db, id)
    if not can_view_study(study, user):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Study not found.")
    return study


def _assert_can_review(study: Study, user: User) -> None:
    if not can_review_study(study, user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only quality checkers can do this, once the study was submitted.",
        )


def _can_respond(study: Study, user: User) -> bool:
    return can_edit_study(study, user)


async def _read(db: AsyncSession, study: Study, user: User) -> StudyReviewRead:
    comments = await review.list_comments(db, study.id)
    return StudyReviewRead(
        study_id=study.id,
        status=study.review_status,
        rounds=await review.list_rounds(db, study.id),
        comments=comments,
        progress=review.progress_of(c.status for c in comments),
        sections=[ReviewSection(key=s.key, label=s.label) for s in COMMENT_SECTIONS],
        can_review=can_review_study(study, user),
        can_respond=_can_respond(study, user),
    )


@router.get("/review-queue", response_model=List[ReviewQueueEntry])
async def get_review_queue(
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_quality_checker),
):
    """Studies submitted for quality check, and those sent back for changes."""
    studies = list(
        (
            await db.execute(
                select(Study).where(
                    Study.review_status.in_(
                        [ReviewStatus.IN_REVIEW.value, ReviewStatus.CHANGES_REQUESTED.value]
                    )
                )
            )
        ).scalars()
    )
    progress = await review.progress_by_study(db, [s.id for s in studies])
    entries = []
    for study in studies:
        current = await review.latest_round(db, study.id)
        entries.append(
            ReviewQueueEntry(
                study_id=study.id,
                title=study.title,
                laboratory_name=study.laboratory.laboratory_name if study.laboratory else None,
                year=study.year,
                status=study.review_status,
                round_number=current.number if current else 0,
                submitted_at=current.submitted_at if current else None,
                progress=progress[study.id],
            )
        )
    return entries


@router.get("/{id}/review", response_model=StudyReviewRead)
async def get_review(
    id: UUID,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    study = await _study(db, id, user)
    if not (can_review_study(study, user) or _can_respond(study, user)):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Study not found.")
    return await _read(db, study, user)


@router.post("/{id}/review/submit", response_model=StudyReviewRead)
async def submit_for_review(
    id: UUID,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    """Submit the study for quality check, or resubmit it after changes."""
    study = await _study(db, id, user)
    assert_can_edit_study(study, user)
    round_ = await review.submit(db, study, user)
    for checker in await crud_user.list_quality_checkers(db):
        if checker.id != user.id and checker.is_active and not checker.invitation_pending:
            await send_study_submitted_for_review_mail(checker, study, round_.number)
    return await _read(db, study, user)


@router.post("/{id}/review/request-changes", response_model=StudyReviewRead)
async def request_changes(
    id: UUID,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_quality_checker),
):
    """Send the study back to its laboratory to address the comments."""
    study = await _study(db, id, user)
    _assert_can_review(study, user)
    await review.request_changes(db, study, user)
    result = await _read(db, study, user)
    if study.laboratory_id is not None:
        for member in await crud_user.list_by_laboratory(db, study.laboratory_id):
            if member.id != user.id and member.is_active and not member.invitation_pending:
                await send_study_changes_requested_mail(member, study, result.progress.open)
    return result


@router.get("/{id}/review/diff", response_model=StudyReviewDiff)
async def get_review_diff(
    id: UUID,
    from_round: int = Query(ge=1),
    to_round: Optional[int] = Query(default=None, ge=1),
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    """What changed between two review rounds, or from a round to the
    study's current data (without `to_round`)."""
    study = await _study(db, id, user)
    if not (can_review_study(study, user) or _can_respond(study, user)):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Study not found.")
    sections = await review.diff(db, study.id, from_round, to_round)
    return StudyReviewDiff(from_round=from_round, to_round=to_round, sections=sections)


@router.get("/{id}/review/records", response_model=StudyReviewRecords)
async def get_review_records(
    id: UUID,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    """The study's records per section, to pin comments to."""
    study = await _study(db, id, user)
    _assert_can_review(study, user)
    return StudyReviewRecords(records=snapshot_records(await take_snapshot(db, study.id)))


@router.post(
    "/{id}/review/comments",
    response_model=StudyReviewRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_comment(
    id: UUID,
    obj_in: CommentCreate,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_quality_checker),
):
    study = await _study(db, id, user)
    _assert_can_review(study, user)
    if obj_in.section not in SECTION_KEYS:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Unknown section.")
    if not obj_in.body.strip():
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "The comment is empty.")
    await review.add_comment(
        db,
        study,
        user,
        body=obj_in.body,
        section=obj_in.section,
        target_id=obj_in.target_id,
        target_label=obj_in.target_label,
        field_label=obj_in.field_label,
    )
    return await _read(db, study, user)


@router.post(
    "/{id}/review/comments/{comment_id}/replies",
    response_model=StudyReviewRead,
    status_code=status.HTTP_201_CREATED,
)
async def reply_to_comment(
    id: UUID,
    comment_id: UUID,
    obj_in: ReplyCreate,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    study = await _study(db, id, user)
    if not (can_review_study(study, user) or _can_respond(study, user)):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You can't reply to this review.")
    parent = await review.get_comment(db, study.id, comment_id)
    if parent.parent_id is not None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Reply to the comment, not to a reply.")
    if not obj_in.body.strip():
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "The reply is empty.")
    await review.add_reply(db, parent, user, obj_in.body)
    return await _read(db, study, user)


@router.patch("/{id}/review/comments/{comment_id}", response_model=StudyReviewRead)
async def update_comment(
    id: UUID,
    comment_id: UUID,
    obj_in: CommentUpdate,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    """Edit a comment's text (its author), or change its status: the
    laboratory marks it addressed, quality checkers resolve or reopen it."""
    study = await _study(db, id, user)
    can_review = can_review_study(study, user)
    can_respond = _can_respond(study, user)
    if not (can_review or can_respond):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You can't change this review.")
    comment = await review.get_comment(db, study.id, comment_id)
    await review.update_comment(
        db,
        comment,
        user,
        body=obj_in.body,
        new_status=obj_in.status,
        can_review=can_review,
        can_respond=can_respond,
    )
    return await _read(db, study, user)


@router.delete("/{id}/review/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    id: UUID,
    comment_id: UUID,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    study = await _study(db, id, user)
    comment = await review.get_comment(db, study.id, comment_id)
    await review.delete_comment(db, comment, user)
