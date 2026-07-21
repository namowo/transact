from typing import List, Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import (
    current_active_user,
    current_optional_user,
    current_quality_checker,
    get_async_session,
)
from app.crud.exceptions import AuthorizationError, NotFoundError
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


def _can_view(study: Study, user: Optional[User]) -> bool:
    if study.published:
        return True
    if user is None:
        return False
    return user.is_superuser or study.laboratory_id == user.laboratory_id


@router.get("", response_model=List[ReadSchema])
async def get_all(
    db: AsyncSession = Depends(get_async_session),
    user: Optional[User] = Depends(current_optional_user),
):
    studies = await crud.get_all(db)
    return [study for study in studies if _can_view(study, user)]


@router.get("/{id}", response_model=ReadSchema)
async def get_by_id(
    id: int,
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


@router.post("/{id}/quality-check", response_model=ReadSchema)
async def pass_quality_check(
    id: int,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_quality_checker),
):
    study = await crud.get(db, id)
    return await crud.pass_quality_check(db, study, user)
