from typing import List, Optional

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import (
    assert_manages_laboratory,
    current_lab_admin,
    current_optional_user,
    current_superuser,
    get_async_session,
)
from app.crud.laboratory import crud_laboratory as crud
from app.crud.user import crud_user
from app.models.user import User
from app.schemas.laboratory import (
    LaboratoryRead as ReadSchema,
    LaboratoryCreate as CreateSchema,
    LaboratoryUpdate as UpdateSchema,
)
from app.schemas.user import UserRead
from app.schemas.planning_checklist import PlanningChecklistRead, PlanningChecklistUpdate
from app.services.planning_checklist import get_sections, reset_sections, save_sections

router = APIRouter()


@router.get("", response_model=List[ReadSchema])
async def get_all(
    db: AsyncSession = Depends(get_async_session),
    user: Optional[User] = Depends(current_optional_user),
):
    if user and user.is_superuser:
        return await crud.get_all(db)
    return await crud.list_approved(db)


@router.get("/{id}", response_model=ReadSchema)
async def get_by_id(id: UUID, db: AsyncSession = Depends(get_async_session)):
    return await crud.get(db, id)


@router.post(
    "",
    response_model=ReadSchema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(current_superuser)],
)
async def create(obj_in: CreateSchema, db: AsyncSession = Depends(get_async_session)):
    # Superuser-only direct creation (e.g. seeding/import). Ordinary users
    # request a new laboratory via the lab-membership-requests endpoints.
    return await crud.create(db, obj_in)


@router.patch(
    "/{id}",
    response_model=ReadSchema,
    dependencies=[Depends(current_superuser)],
)
async def update(
    id: UUID, obj_in: UpdateSchema, db: AsyncSession = Depends(get_async_session)
):
    return await crud.update(db, id, obj_in)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(current_superuser)],
)
async def delete(id: UUID, db: AsyncSession = Depends(get_async_session)):
    await crud.delete(db, id)


@router.get("/{id}/users", response_model=List[UserRead])
async def get_lab_users(
    id: UUID,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_lab_admin),
):
    assert_manages_laboratory(user, id)
    return await crud_user.list_by_laboratory(db, id)


# --- Planning checklist -----------------------------------------------------
# Lab admins replace the default planning checklist with their laboratory's
# own; studies of the laboratory then show it (see GET /studies/{id}/planning-checklist).


@router.put("/{id}/planning-checklist", response_model=PlanningChecklistRead)
async def save_planning_checklist(
    id: UUID,
    obj_in: PlanningChecklistUpdate,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_lab_admin),
):
    assert_manages_laboratory(user, id)
    await crud.get(db, id)  # 404 for unknown laboratories
    await save_sections(db, id, [section.model_dump() for section in obj_in.sections])
    sections, is_default = await get_sections(db, id)
    return PlanningChecklistRead(laboratory_id=id, sections=sections, is_default=is_default, can_edit=True)


@router.delete("/{id}/planning-checklist", response_model=PlanningChecklistRead)
async def reset_planning_checklist(
    id: UUID,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_lab_admin),
):
    """Go back to the default checklist."""
    assert_manages_laboratory(user, id)
    await reset_sections(db, id)
    sections, is_default = await get_sections(db, id)
    return PlanningChecklistRead(laboratory_id=id, sections=sections, is_default=is_default, can_edit=True)
