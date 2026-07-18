from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import current_active_user, get_async_session
from app.crud.exceptions import AuthorizationError
from app.crud.study import crud_study as crud
from app.models.study import Study
from app.models.user import User
from app.schemas.study import (
    StudyRead as ReadSchema,
    StudyCreate as CreateSchema,
    StudyUpdate as UpdateSchema,
)

router = APIRouter()


def _assert_can_edit(study: Study, user: User) -> None:
    if not user.is_superuser and study.laboratory_id != user.laboratory_id:
        raise AuthorizationError(
            message="You can only edit studies belonging to your own laboratory."
        )


@router.get("", response_model=List[ReadSchema])
async def get_all(db: AsyncSession = Depends(get_async_session)):
    return await crud.get_all(db)


@router.get("/{id}", response_model=ReadSchema)
async def get_by_id(id: int, db: AsyncSession = Depends(get_async_session)):
    return await crud.get(db, id)


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
    # Non-superusers can only create studies for their own laboratory,
    # regardless of what laboratory_id was submitted.
    if not user.is_superuser:
        obj_in = obj_in.model_copy(update={"laboratory_id": user.laboratory_id})
    return await crud.create(db, obj_in)


@router.patch(
    "/{id}",
    response_model=ReadSchema,
)
async def update(
    id: int,
    obj_in: UpdateSchema,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    study = await crud.get(db, id)
    _assert_can_edit(study, user)
    return await crud.update(db, id, obj_in)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete(
    id: int,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    study = await crud.get(db, id)
    _assert_can_edit(study, user)
    await crud.delete(db, id)
