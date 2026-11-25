from typing import List, Optional

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import (
    assert_manages_laboratory,
    current_active_user,
    current_laboratory_manager,
    current_member_manager,
    current_optional_user,
    get_async_session,
)
from app.core.permission_catalog import Permission
from app.crud.laboratory import crud_laboratory as crud
from app.crud.user import crud_user
from app.models.user import User
from app.schemas.laboratory import (
    LaboratoryRead as ReadSchema,
    LaboratoryCreate as CreateSchema,
    LaboratoryUpdate as UpdateSchema,
    LaboratoryDataAccessUpdate,
)
from app.schemas.user import UserRead
from app.schemas.planning_checklist import PlanningChecklistRead, PlanningChecklistUpdate
from app.services.planning_checklist import get_sections, reset_sections, save_sections

router = APIRouter()


def _assert_manages_settings(user: User, laboratory_id: UUID) -> None:
    if not user.can_in_laboratory(Permission.MANAGE_LAB_SETTINGS, laboratory_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only change the settings of your own laboratory.",
        )


@router.get("", response_model=List[ReadSchema])
async def get_all(
    db: AsyncSession = Depends(get_async_session),
    user: Optional[User] = Depends(current_optional_user),
):
    if user and user.can(Permission.MANAGE_LABORATORIES):
        return await crud.get_all(db)
    return await crud.list_approved(db)


@router.get("/{id}", response_model=ReadSchema)
async def get_by_id(id: UUID, db: AsyncSession = Depends(get_async_session)):
    return await crud.get(db, id)


@router.post(
    "",
    response_model=ReadSchema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(current_laboratory_manager)],
)
async def create(obj_in: CreateSchema, db: AsyncSession = Depends(get_async_session)):
    # Direct creation by laboratory managers, e.g. to prepare a laboratory's
    # data before anyone joins it. Ordinary users request a new laboratory
    # via the lab-membership-requests endpoints.
    return await crud.create(db, obj_in)


@router.patch(
    "/{id}",
    response_model=ReadSchema,
    dependencies=[Depends(current_laboratory_manager)],
)
async def update(
    id: UUID, obj_in: UpdateSchema, db: AsyncSession = Depends(get_async_session)
):
    # Only the fields sent change; a field sent as null is cleared.
    return await crud.update(db, id, obj_in, exclude_none=False)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(current_laboratory_manager)],
)
async def delete(id: UUID, db: AsyncSession = Depends(get_async_session)):
    await crud.delete(db, id)


@router.get("/{id}/users", response_model=List[UserRead])
async def get_lab_users(
    id: UUID,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_member_manager),
):
    assert_manages_laboratory(user, id)
    return await crud_user.list_by_laboratory(db, id)


@router.put("/{id}/data-access", response_model=ReadSchema)
async def set_data_access(
    id: UUID,
    obj_in: LaboratoryDataAccessUpdate,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    """Let platform admins with "Edit data of all laboratories" work on this
    laboratory's studies - or stop them. Up to the laboratory itself."""
    if not user.can_in_laboratory(Permission.MANAGE_LAB_SETTINGS, id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the laboratory's own admins can change this.",
        )
    laboratory = await crud.get(db, id)
    laboratory.allow_admin_data_entry = obj_in.allow_admin_data_entry
    await db.commit()
    await db.refresh(laboratory)
    return laboratory


# --- Planning checklist -----------------------------------------------------
# Lab admins replace the default planning checklist with their laboratory's
# own; studies of the laboratory then show it (see GET /studies/{id}/planning-checklist).


@router.put("/{id}/planning-checklist", response_model=PlanningChecklistRead)
async def save_planning_checklist(
    id: UUID,
    obj_in: PlanningChecklistUpdate,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    _assert_manages_settings(user, id)
    await crud.get(db, id)  # 404 for unknown laboratories
    await save_sections(db, id, [section.model_dump() for section in obj_in.sections])
    sections, is_default = await get_sections(db, id)
    return PlanningChecklistRead(laboratory_id=id, sections=sections, is_default=is_default, can_edit=True)


@router.delete("/{id}/planning-checklist", response_model=PlanningChecklistRead)
async def reset_planning_checklist(
    id: UUID,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    """Go back to the default checklist."""
    _assert_manages_settings(user, id)
    await reset_sections(db, id)
    sections, is_default = await get_sections(db, id)
    return PlanningChecklistRead(laboratory_id=id, sections=sections, is_default=is_default, can_edit=True)
