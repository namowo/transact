from typing import List, Optional

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import (
    current_active_user,
    current_optional_user,
    current_data_editor,
    current_quality_checker,
    get_async_session,
)
from app.core.permission_catalog import Permission
from app.core.permissions import (
    assert_can_edit_studies,
    assert_can_edit_study,
    can_create_study_for,
    can_edit_study,
    can_view_study,
)
from app.crud.laboratory import crud_laboratory
from app.crud.exceptions import NotFoundError
from app.crud.study import crud_study as crud
from app.crud.user import crud_user
from app.services import study_review
from app.services.mail.messages import send_study_quality_checked_mail
from app.models.user import User
from app.services.data_export.writers import attachment_headers, iter_file
from app.schemas.planning_checklist import PlanningChecklistProgress, PlanningChecklistRead
from app.services.planning_checklist import (
    can_edit_checklist,
    get_progress,
    get_sections,
    save_progress,
)
from app.services.planning_sheet import (
    XLSX_MEDIA_TYPE,
    NeedsConfirmationError,
    PlanningSheetError,
    apply_planning_sheet,
    build_planning_sheet,
)
from app.schemas.study import (
    StudyRead as ReadSchema,
    StudyCreate as CreateSchema,
    StudyUpdate as UpdateSchema,
)

router = APIRouter()


_can_view = can_view_study


async def _assert_can_create_for(
    db: AsyncSession, user: User, laboratory_id: Optional[UUID]
) -> None:
    laboratory = None
    if laboratory_id is not None:
        try:
            laboratory = await crud_laboratory.get(db, laboratory_id)
        except NotFoundError:
            laboratory = None
    if not can_create_study_for(user, laboratory):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can't add studies to this laboratory.",
        )


@router.get("", response_model=List[ReadSchema])
async def get_all(
    db: AsyncSession = Depends(get_async_session),
    user: Optional[User] = Depends(current_optional_user),
):
    studies = await crud.get_all(db)
    return [study for study in studies if _can_view(study, user)]


@router.get("/{id}", response_model=ReadSchema)
async def get_by_id(
    id: UUID,
    db: AsyncSession = Depends(get_async_session),
    user: Optional[User] = Depends(current_optional_user),
):
    study = await crud.get(db, id)
    if not _can_view(study, user):
        raise NotFoundError(status_code=status.HTTP_404_NOT_FOUND, message="Study not found.")
    return study


@router.post(
    "",
    response_model=ReadSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create(
    obj_in: CreateSchema,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    # Studies go to the user's own laboratory unless they may act for the
    # requested one (see app.core.permissions).
    if obj_in.laboratory_id is None or obj_in.laboratory_id == user.laboratory_id:
        obj_in = obj_in.model_copy(update={"laboratory_id": user.laboratory_id})
    await _assert_can_create_for(db, user, obj_in.laboratory_id)
    return await crud.create(db, obj_in)


@router.patch(
    "/{id}",
    response_model=ReadSchema,
)
async def update(
    id: UUID,
    obj_in: UpdateSchema,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    study = await crud.get(db, id)
    assert_can_edit_study(study, user)
    # Moving a study to another laboratory is up to laboratory managers, and
    # only into a laboratory they could create the study in.
    if obj_in.laboratory_id is not None and obj_in.laboratory_id != study.laboratory_id:
        if not user.can(Permission.MANAGE_LABORATORIES):
            obj_in = obj_in.model_copy(update={"laboratory_id": None})
        else:
            await _assert_can_create_for(db, user, obj_in.laboratory_id)
    return await crud.update(db, id, obj_in)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete(
    id: UUID,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    study = await crud.get(db, id)
    assert_can_edit_study(study, user)
    await crud.delete(db, id)


@router.post("/{id}/quality-check", response_model=ReadSchema)
async def pass_quality_check(
    id: UUID,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_quality_checker),
):
    study = await crud.get(db, id)
    already_passed = study.quality_check_passed
    # Every comment of the review has to be resolved first.
    await study_review.assert_can_pass(db, study)
    await study_review.mark_passed(db, study, user)
    study = await crud.pass_quality_check(db, study, user)

    if not already_passed and study.laboratory_id is not None:
        for member in await crud_user.list_by_laboratory(db, study.laboratory_id):
            if member.id != user.id and member.is_active and not member.invitation_pending:
                await send_study_quality_checked_mail(member, study)

    return study


# 10 MB is far more than a planning sheet with a few hundred rows needs.
MAX_PLANNING_SHEET_BYTES = 10 * 1024 * 1024


@router.get("/{id}/planning-sheet")
async def download_planning_sheet(
    id: UUID,
    db: AsyncSession = Depends(get_async_session),
    user: Optional[User] = Depends(current_optional_user),
):
    """The planning checklist as .xlsx, with sheets to plan the study's
    individuals and items. Upload it again to add them to the study."""
    study = await crud.get(db, id)
    if not _can_view(study, user):
        raise NotFoundError(status_code=status.HTTP_404_NOT_FOUND, message="Study not found.")
    workbook = await build_planning_sheet(db, study)
    return StreamingResponse(
        iter_file(workbook),
        media_type=XLSX_MEDIA_TYPE,
        headers=attachment_headers(f"{study.title or 'study'} planning checklist", "xlsx"),
    )


@router.post("/{id}/planning-sheet")
async def upload_planning_sheet(
    id: UUID,
    request: Request,
    create_categories: bool = False,
    scenario_ids: List[UUID] = Query(default=[]),
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_data_editor),
):
    """Create/update the study's individuals and items from a filled-in
    planning sheet (sent as the raw .xlsx request body). All or nothing:
    any invalid row rejects the whole file with a list of problems.

    Answered with 409 when the user has to decide first: item categories the
    catalog doesn't have yet (upload again with `create_categories=true`), or
    rows without a scenario (upload again with the `scenario_ids` to assign)."""
    study = await crud.get(db, id)
    await assert_can_edit_studies(db, user, {study.id})
    content = await request.body()
    if len(content) > MAX_PLANNING_SHEET_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="This file is too large.")
    try:
        summary = await apply_planning_sheet(
            db,
            study,
            content,
            create_categories=create_categories,
            default_scenario_ids=scenario_ids,
        )
    except NeedsConfirmationError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": "The planning sheet needs confirmation.",
                "new_categories": error.categories,
                "new_subcategories": error.subcategories,
                "unassigned_individuals": error.unassigned_individuals,
                "unassigned_items": error.unassigned_items,
            },
        ) from None
    except PlanningSheetError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={"message": "The planning sheet has problems.", "errors": error.errors},
        ) from None
    return summary


@router.get("/{id}/planning-checklist", response_model=PlanningChecklistRead)
async def get_planning_checklist(
    id: UUID,
    db: AsyncSession = Depends(get_async_session),
    user: Optional[User] = Depends(current_optional_user),
):
    """The planning checklist of the study's laboratory (or the default)."""
    study = await crud.get(db, id)
    if not _can_view(study, user):
        raise NotFoundError(status_code=status.HTTP_404_NOT_FOUND, message="Study not found.")
    sections, is_default = await get_sections(db, study.laboratory_id)
    checked, notes = await get_progress(db, study.id)
    return PlanningChecklistRead(
        laboratory_id=study.laboratory_id,
        sections=sections,
        is_default=is_default,
        checked=checked,
        notes=notes,
        can_edit=can_edit_checklist(user, study.laboratory_id),
        can_check=can_edit_study(study, user),
    )


@router.put("/{id}/planning-checklist/progress", response_model=PlanningChecklistProgress)
async def save_planning_checklist_progress(
    id: UUID,
    obj_in: PlanningChecklistProgress,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    """Tick items off the study's planning checklist and keep notes on them.
    Members of the study's laboratory only."""
    study = await crud.get(db, id)
    assert_can_edit_study(study, user)
    checked, notes = await save_progress(db, study.id, study.laboratory_id, obj_in.checked, obj_in.notes)
    return PlanningChecklistProgress(checked=checked, notes=notes)
